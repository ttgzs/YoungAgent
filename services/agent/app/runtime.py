import asyncio, json, uuid
from .tools import ToolRegistry, Tool
from .model_router import ModelRouter
from .db import save_task, save_event
from .approval import ApprovalGate
from .adapters import MCPClient, BrowserAdapter, ComputerUseAdapter
from .orchestrator import AgentOrchestrator, default_packages
from .security import Principal, AuditLog, allowed
from .skills import SkillRegistry
from .config import settings
from .checkpoint import save_checkpoint

class AgentRuntime:
    def __init__(self):
        self.tools=ToolRegistry(); self.model=ModelRouter(); self.approval=ApprovalGate(); self.mcp=MCPClient(); self.browser=BrowserAdapter(); self.computer=ComputerUseAdapter(); self.audit=AuditLog(); self.skills=SkillRegistry(); self._register_native()
    def _register_native(self):
        from .tools import fs_read, fs_list, python_sandbox
        self.tools.register(Tool('filesystem.read','读取文本文件',fs_read))
        self.tools.register(Tool('filesystem.list','列出目录',fs_list))
        self.tools.register(Tool('python.sandbox','隔离目录运行 Python',python_sandbox))

    def tool_schemas(self):
        schemas=[]
        for t in self.tools.list():
            schemas.append({'type':'function','function':{'name':t.name,'description':t.description,'parameters':{'type':'object','properties':self._parameters(t.name),'additionalProperties':False}}})
        return schemas

    def _parameters(self,name):
        return {
            'filesystem.read': {'path':{'type':'string','description':'文件路径'}},
            'filesystem.list': {'path':{'type':'string','description':'目录路径'}},
            'python.sandbox': {'code':{'type':'string','description':'Python代码'}}
        }.get(name,{})

    async def _execute_tool_call(self, call, principal, emit=None):
        fn=call.get('function',{})
        name=fn.get('name'); raw=fn.get('arguments') or '{}'
        try: args=json.loads(raw) if isinstance(raw,str) else raw
        except Exception as e: return {'error':f'工具参数JSON无效: {e}'}
        tool=self.tools.get(name)
        if not tool: return {'error':f'未知工具: {name}'}
        if tool.requires_approval:
            aid=self.approval.request(name,args)
            if emit: await emit('approval.required',{'approval_id':aid,'tool':name,'arguments':args})
            return {'approval_required':True,'approval_id':aid}
        if emit: await emit('tool.start',{'tool':name,'arguments':args})
        try:
            result=await asyncio.wait_for(tool.handler(**args), timeout=settings.tool_timeout_seconds)
            if emit: await emit('tool.finish',{'tool':name,'result':result})
            self.audit.record('tool.execute',principal,name,'completed')
            return result
        except Exception as e:
            if emit: await emit('tool.error',{'tool':name,'error':str(e)})
            self.audit.record('tool.execute',principal,name,'failed')
            return {'error':str(e)}

    async def _model_runner(self,agent_type,prompt,principal=None,emit=None,task_id=None):
        principal=principal or Principal()
        skill={'research':'research','planner':'project-management','security':None}.get(agent_type)
        sys='你是企业 Agent 子智能体。输出简洁、结构化、可审计。'
        if skill: sys+='\n'+self.skills.prompt([skill])
        messages=[{'role':'system','content':sys},{'role':'user','content':prompt}]
        for step in range(settings.max_steps):
            r=await self.model.chat(messages,self.tool_schemas())
            if task_id: await save_checkpoint(task_id, step+1, {'agent_type':agent_type,'messages':messages[-4:]})
            if emit: await emit('model.step',{'agent_type':agent_type,'step':step+1,'finish_reason':r.get('finish_reason'),'usage':r.get('usage')})
            calls=r.get('tool_calls') or []
            if not calls: return r['content']
            messages.append(r['message'])
            for call in calls:
                result=await self._execute_tool_call(call,principal,emit)
                messages.append({'role':'tool','tool_call_id':call.get('id',''),'name':call.get('function',{}).get('name',''),'content':json.dumps(result,ensure_ascii=False,default=str)})
                if result.get('approval_required'): return json.dumps(result,ensure_ascii=False)
        return '达到 Agent 最大工具调用步数，任务未完成。'

    async def run(self,task,task_id=None,principal=None):
        principal=principal or Principal(); task_id=task_id or uuid.uuid4().hex
        if not allowed(principal,'task.run'): raise PermissionError('无 task.run 权限')
        await save_task(task_id,task,'running',tenant_id=principal.tenant_id,user_id=principal.user_id); events=[]
        async def emit(t,d): events.append({'type':t,'data':d}); await save_event(task_id,t,d,principal.tenant_id)
        self.audit.record('task.run',principal,task_id,'started')
        packages=default_packages(task)
        await emit('plan',{'mode':'parallel-dag','packages':[p.__dict__ for p in packages]})
        result=await AgentOrchestrator(lambda a,p:self._model_runner(a,p,principal,emit,task_id)).run(packages,emit)
        completed=[v for v in result.values() if v['status']=='completed']
        output=result.get('synthesis',{}).get('output') or (completed[-1]['output'] if completed else '任务执行失败，请检查子智能体结果。')
        status='completed' if len(completed)==len(result)==4 else 'partial'
        await emit('finish',{'output':output,'status':status,'subagents':result})
        final={'status':status,'task_id':task_id,'output':output,'subagents':result,'steps':events}
        await save_task(task_id,task,status,final,principal.tenant_id,principal.user_id); self.audit.record('task.run',principal,task_id,status)
        return final
