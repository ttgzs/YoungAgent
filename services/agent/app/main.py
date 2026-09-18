import json
from fastapi import FastAPI,HTTPException,Query,Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from .runtime import AgentRuntime
from .db import init_db,get_task,get_events,save_task
from .security import Principal
from .queue import queue
from .checkpoint import latest_checkpoint
from .rag import add_document,search_documents
from .rag_engine import index_document,semantic_search
from .management import catalog
from .authz import principal_from_header, require
from .auth import issue_token
from .rate_limit import rate_limiter
from .metrics import metrics
from .marketplace import marketplace, installed_packs
from .domain_agents import project_schedule, schedule_variance, parse_ifc_summary, extract_ifc_properties, water_kpis, aeration_recommendation, telemetry_summary, alarm_rules
app=FastAPI(title='YoungAgent Enterprise Agent OS',version='3.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
runtime=AgentRuntime()
@app.on_event('startup')
async def startup():
    from . import rag_engine  # register ORM models
    from .workflow import repository  # register workflow ORM
    await init_db()
class AgentRequest(BaseModel): task:str=Field(min_length=1,max_length=50000); task_id:str|None=None; user_id:str='anonymous'; tenant_id:str='default'; roles:list[str]=['user']
class ApprovalRequest(BaseModel): approval_id:str
class LoginRequest(BaseModel): user_id:str='anonymous'; tenant_id:str='default'; roles:list[str]=['user']
class DocumentRequest(BaseModel): title:str; content:str
@app.get('/metrics')
async def get_metrics(): return metrics.snapshot()


class ProjectTasksRequest(BaseModel):
    tasks:list[dict]
class ScheduleVarianceRequest(BaseModel):
    planned_finish:str; actual_finish:str|None=None; today:str|None=None
class IFCRequest(BaseModel):
    content:str
class WaterSamplesRequest(BaseModel):
    samples:list[dict]
    target_do:float=2.0
class TelemetryRequest(BaseModel):
    points:list[dict]
    high:float|None=None
    low:float|None=None

@app.post('/api/v1/domain/project/schedule')
async def project_schedule_api(req:ProjectTasksRequest):
    return {'items':project_schedule(req.tasks)}
@app.post('/api/v1/domain/project/variance')
async def project_variance_api(req:ScheduleVarianceRequest):
    return schedule_variance(req.planned_finish,req.actual_finish,req.today)
@app.post('/api/v1/domain/bim/ifc/summary')
async def bim_ifc_summary(req:IFCRequest):
    return parse_ifc_summary(req.content)
@app.post('/api/v1/domain/bim/ifc/entities')
async def bim_ifc_entities(req:IFCRequest,limit:int=Query(100,ge=1,le=1000)):
    return {'items':extract_ifc_properties(req.content,limit)}
@app.post('/api/v1/domain/water/kpis')
async def water_kpi_api(req:WaterSamplesRequest):
    return {'kpis':water_kpis(req.samples),'aeration':aeration_recommendation(req.samples,req.target_do)}
@app.post('/api/v1/domain/iot/telemetry/summary')
async def iot_summary_api(req:TelemetryRequest):
    return {'items':telemetry_summary(req.points),'alarms':alarm_rules(req.points,req.high,req.low)}

@app.get('/health')
async def health(): return {'status':'ok','version':'3.3.0','features':['async-worker','checkpoint-resume','retry','tool-calling','multi-agent','mcp','rag','rbac','audit','browser','computer-use','marketplace','domain-agents']}
@app.post('/api/v1/auth/token')
async def token(req:LoginRequest): return {'access_token':issue_token(req.user_id,req.tenant_id,req.roles),'token_type':'bearer'}

@app.get('/api/v1/me')
async def me(principal=__import__('fastapi').Depends(principal_from_header)): return {'user_id':principal.user_id,'tenant_id':principal.tenant_id,'roles':list(principal.roles)}
@app.get('/api/v1/tools')
async def tools(): return {'tools':[{'name':t.name,'description':t.description,'risk':t.risk,'requires_approval':t.requires_approval} for t in runtime.tools.list()],'skills':[s.name for s in runtime.skills.list()]}
@app.post('/api/v1/agent/submit')
async def submit(req:AgentRequest):
    if not rate_limiter.allow(f'{req.tenant_id}:{req.user_id}'): raise HTTPException(429,'请求频率超过限制')
    metrics.inc('tasks.submitted')
    tid=req.task_id or __import__('uuid').uuid4().hex; await save_task(tid,req.task,'queued',None,req.tenant_id,req.user_id); await queue.enqueue({'task_id':tid,'task':req.task,'user_id':req.user_id,'tenant_id':req.tenant_id,'roles':req.roles}); return {'task_id':tid,'status':'queued'}
@app.post('/api/v1/agent/run')
async def run_agent(req:AgentRequest):
    if not rate_limiter.allow(f'{req.tenant_id}:{req.user_id}'): raise HTTPException(429,'请求频率超过限制')
    metrics.inc('tasks.sync_run')
    try:return await runtime.run(req.task,req.task_id,Principal(req.user_id,req.tenant_id,tuple(req.roles)))
    except PermissionError as e: raise HTTPException(403,str(e))
    except Exception as e: raise HTTPException(500,f'Agent execution failed: {e}')
@app.post('/api/v1/tasks/{task_id}/retry')
async def retry(task_id:str,tenant_id:str=Query('default'),user_id:str=Query('anonymous')):
    obj=await get_task(task_id,tenant_id)
    if not obj: raise HTTPException(404,'任务不存在')
    await save_task(task_id,obj['prompt'],'queued',None,tenant_id,user_id); await queue.enqueue({'task_id':task_id,'task':obj['prompt'],'user_id':user_id,'tenant_id':tenant_id,'roles':['user']}); return {'task_id':task_id,'status':'queued'}
@app.get('/api/v1/tasks/{task_id}')
async def task_get(task_id:str,tenant_id:str=Query('default')):
    obj=await get_task(task_id,tenant_id)
    if not obj: raise HTTPException(404,'任务不存在')
    obj['checkpoint']=await latest_checkpoint(task_id); return obj
@app.get('/api/v1/tasks/{task_id}/events')
async def task_events(task_id:str,tenant_id:str=Query('default')):
    if not await get_task(task_id,tenant_id): raise HTTPException(404,'任务不存在')
    return {'items':await get_events(task_id,tenant_id)}
@app.post('/api/v1/approval/request')
async def approval_request(payload:dict): return {'approval_id':runtime.approval.request(payload.get('action','unknown'),payload)}
@app.post('/api/v1/approval/approve')
async def approval_approve(req:ApprovalRequest): return runtime.approval.approve(req.approval_id) or {'error':'not_found'}
@app.get('/api/v1/approval/{approval_id}')
async def approval_get(approval_id:str): return runtime.approval.get(approval_id) or {'error':'not_found'}
@app.get('/api/v1/audit')
async def audit(tenant_id:str=Query('default')): return {'items':runtime.audit.list(tenant_id)}
@app.post('/api/v1/knowledge/documents')
async def knowledge_add(req:DocumentRequest,tenant_id:str=Query('default')):
    await add_document(tenant_id,req.title,req.content)
    from .db import Session
    from .rag import Document
    async with Session() as s:
        from sqlalchemy import select
        r=await s.execute(select(Document).where(Document.tenant_id==tenant_id,Document.title==req.title).order_by(Document.id.desc()))
        d=r.scalars().first()
    if d: await index_document(tenant_id,d.id,req.title,req.content)
    return {'status':'ok','document_id':d.id if d else None}
@app.get('/api/v1/knowledge/search')
async def knowledge_search(q:str,tenant_id:str=Query('default')): return {'items':await search_documents(tenant_id,q)}


class AgentDefinitionRequest(BaseModel):
    name:str=Field(min_length=1,max_length=100); description:str=''; model:str=''; system_prompt:str=''

@app.get('/api/v1/admin/agents')
async def admin_agents(principal=__import__('fastapi').Depends(principal_from_header)):
    require(principal,'admin.manage'); return {'items':catalog.list(principal.tenant_id)}

@app.post('/api/v1/admin/agents')
async def admin_agent_create(req:AgentDefinitionRequest,principal=__import__('fastapi').Depends(principal_from_header)):
    require(principal,'admin.manage'); return catalog.create(principal.tenant_id,req.name,req.description,req.model,req.system_prompt)

@app.delete('/api/v1/admin/agents/{agent_id}')
async def admin_agent_delete(agent_id:str,principal=__import__('fastapi').Depends(principal_from_header)):
    require(principal,'admin.manage')
    if not catalog.delete(agent_id,principal.tenant_id): raise HTTPException(404,'agent not found')
    return {'status':'deleted'}

@app.get('/api/v1/marketplace/packs')
async def marketplace_packs(category:str|None=None):
    return {'items':marketplace.list(category)}

@app.get('/api/v1/marketplace/packs/{pack_id}')
async def marketplace_pack(pack_id:str):
    item=marketplace.get(pack_id)
    if not item: raise HTTPException(404,'pack not found')
    return item

@app.post('/api/v1/marketplace/packs/{pack_id}/install')
async def marketplace_install(pack_id:str,tenant_id:str=Query('default')):
    result=marketplace.install(pack_id,tenant_id,installed_packs)
    if not result: raise HTTPException(404,'pack not found')
    return result

@app.get('/api/v1/marketplace/installed')
async def marketplace_installed(tenant_id:str=Query('default')):
    return {'items':marketplace.installed(tenant_id,installed_packs)}

@app.get('/api/v1/knowledge/semantic-search')
async def knowledge_semantic(q:str,tenant_id:str=Query('default'),limit:int=Query(5,ge=1,le=20)): return {'items':await semantic_search(tenant_id,q,limit)}

# V4.0 Agentic Workflow: domain business loop with DAG + Approval Gate.
from .workflow.engine import WorkflowEngine
from .workflow.domain_handlers import handlers as workflow_handlers
from .workflow.repository import save_workflow, load_workflow, list_workflows
from .workflow.designer import validate_definition, template
workflow_engine=WorkflowEngine(workflow_handlers())
class WorkflowStepRequest(BaseModel):
    id:str; name:str; action:str; depends_on:list[str]=[]; requires_approval:bool=False; max_attempts:int=3
class WorkflowCreateRequest(BaseModel):
    name:str=Field(min_length=1,max_length=200); steps:list[WorkflowStepRequest]
class WorkflowExecuteRequest(BaseModel):
    context:dict={}
class WorkflowApproveRequest(BaseModel):
    context:dict={}

@app.post('/api/v1/workflows')
async def workflow_create(req:WorkflowCreateRequest):
    try: wf=workflow_engine.create(req.name,[x.model_dump() for x in req.steps]); await save_workflow(workflow_engine.serialize(wf)); return workflow_engine.serialize(wf)
    except ValueError as e: raise HTTPException(400,str(e))

@app.get('/api/v1/workflows/{workflow_id}')
async def workflow_get(workflow_id:str):
    wf=workflow_engine.workflows.get(workflow_id)
    if not wf:
        payload=await load_workflow(workflow_id)
        if payload: wf=workflow_engine.restore(payload)
    if not wf: raise HTTPException(404,'workflow_not_found')
    return workflow_engine.serialize(wf)

@app.post('/api/v1/workflows/{workflow_id}/execute')
async def workflow_execute(workflow_id:str,req:WorkflowExecuteRequest):
    if workflow_id not in workflow_engine.workflows: raise HTTPException(404,'workflow_not_found')
    wf=workflow_engine.execute(workflow_id,req.context); await save_workflow(workflow_engine.serialize(wf)); return workflow_engine.serialize(wf)

@app.post('/api/v1/workflows/{workflow_id}/steps/{step_id}/approve')
async def workflow_approve(workflow_id:str,step_id:str,req:WorkflowApproveRequest):
    try: wf=workflow_engine.approve_and_resume(workflow_id,step_id,req.context); await save_workflow(workflow_engine.serialize(wf)); return workflow_engine.serialize(wf)
    except KeyError: raise HTTPException(404,'workflow_or_step_not_found')
    except ValueError as e: raise HTTPException(400,str(e))

@app.get('/api/v1/workflows')
async def workflow_list(tenant_id:str=Query('default')): return {'items':await list_workflows(tenant_id)}

@app.post('/api/v1/workflows/{workflow_id}/cancel')
async def workflow_cancel(workflow_id:str,tenant_id:str=Query('default')):
    wf=workflow_engine.workflows.get(workflow_id)
    if not wf:
        payload=await load_workflow(workflow_id)
        if payload: wf=workflow_engine.restore(payload)
    if not wf: raise HTTPException(404,'workflow_not_found')
    wf=workflow_engine.cancel(workflow_id); await save_workflow(workflow_engine.serialize(wf),tenant_id); return workflow_engine.serialize(wf)

class WorkflowRetryRequest(BaseModel): step_id:str|None=None
@app.post('/api/v1/workflows/{workflow_id}/retry')
async def workflow_retry(workflow_id:str,req:WorkflowRetryRequest,tenant_id:str=Query('default')):
    wf=workflow_engine.workflows.get(workflow_id)
    if not wf:
        payload=await load_workflow(workflow_id)
        if payload: wf=workflow_engine.restore(payload)
    if not wf: raise HTTPException(404,'workflow_not_found')
    wf=workflow_engine.retry(workflow_id,req.step_id); await save_workflow(workflow_engine.serialize(wf),tenant_id); return workflow_engine.serialize(wf)

@app.get('/api/v1/workflows/templates/{name}')
async def workflow_template(name:str):
    try: return {'name':name,'steps':template(name)}
    except KeyError: raise HTTPException(404,'template_not_found')

@app.post('/api/v1/workflows/validate')
async def workflow_validate(req:WorkflowCreateRequest):
    try: return validate_definition([x.model_dump() for x in req.steps])
    except ValueError as e: raise HTTPException(400,str(e))

# V4.4-V4.6 Workflow Designer / Trigger / Event Bus
from .workflow.triggers import TriggerRegistry, EventBus
from .workflow.scheduler import WorkflowScheduler
import asyncio
trigger_registry=TriggerRegistry(); event_bus=EventBus()
class TriggerRequest(BaseModel):
    workflow_id:str; kind:str; config:dict={}
class EventRequest(BaseModel):
    event_type:str; payload:dict={}

@app.get('/api/v1/workflows/{workflow_id}/triggers')
async def workflow_triggers(workflow_id:str):
    return {'items':[trigger_registry.serialize(x) for x in trigger_registry.list(workflow_id)]}

@app.post('/api/v1/workflows/triggers')
async def trigger_create(req:TriggerRequest):
    if req.workflow_id not in workflow_engine.workflows:
        payload=await load_workflow(req.workflow_id)
        if payload: workflow_engine.restore(payload)
    if req.workflow_id not in workflow_engine.workflows: raise HTTPException(404,'workflow_not_found')
    try: t=trigger_registry.create(req.workflow_id,req.kind,req.config); return trigger_registry.serialize(t)
    except ValueError as e: raise HTTPException(400,str(e))

@app.delete('/api/v1/workflows/triggers/{trigger_id}')
async def trigger_delete(trigger_id:str):
    if not trigger_registry.delete(trigger_id): raise HTTPException(404,'trigger_not_found')
    return {'status':'deleted'}

@app.post('/api/v1/events/publish')
async def event_publish(req:EventRequest):
    results=await event_bus.publish(req.event_type,req.payload)
    for t in trigger_registry.list():
        if t.enabled and t.kind=='event' and t.config.get('event_type')==req.event_type:
            await _fire_trigger(t); trigger_registry.fired(t)
    return {'event_type':req.event_type,'results':results}


async def _fire_trigger(trigger):
    if trigger.workflow_id not in workflow_engine.workflows:
        payload=await load_workflow(trigger.workflow_id)
        if payload: workflow_engine.restore(payload)
    if trigger.workflow_id in workflow_engine.workflows:
        wf=workflow_engine.execute(trigger.workflow_id, trigger.config.get("context", {}))
        await save_workflow(workflow_engine.serialize(wf), trigger.config.get("tenant_id", "default"))

async def _interval_loop():
    scheduler=WorkflowScheduler(trigger_registry,_fire_trigger)
    await scheduler.run(2)

@app.on_event("startup")
async def start_workflow_scheduler():
    app.state.workflow_scheduler_task=asyncio.create_task(_interval_loop())

@app.on_event("shutdown")
async def stop_workflow_scheduler():
    task=getattr(app.state,'workflow_scheduler_task',None)
    if task:
        task.cancel()
