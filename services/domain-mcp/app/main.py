"""Enterprise domain MCP-compatible connector service.
Deterministic adapters first; vendor-specific connectors can replace these handlers later.
"""
from __future__ import annotations
from datetime import date, timedelta
from statistics import mean
from collections import Counter, defaultdict
import csv, io, re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title='YoungAgent Enterprise Domain MCP', version='3.9.0')
from .connectors import ProjectConnector, BIMConnector, IoTConnector
project_connector=ProjectConnector(); bim_connector=BIMConnector(); iot_connector=IoTConnector()

TOOLS = [
    {'name':'project.schedule_calculate','description':'Calculate project task dates from duration and predecessors.','risk':'read','requires_approval':False},
    {'name':'project.schedule_variance','description':'Calculate planned/actual schedule variance.','risk':'read','requires_approval':False},
    {'name':'project.mpp_xml_summary','description':'Parse Microsoft Project XML export and summarize tasks/dependencies.','risk':'read','requires_approval':False},
    {'name':'bim.ifc_summary','description':'Summarize IFC entity types and counts.','risk':'read','requires_approval':False},
    {'name':'bim.ifc_elements','description':'Extract IFC element records from an IFC text file.','risk':'read','requires_approval':False},
    {'name':'bim.quantity_summary','description':'Aggregate simple numeric quantities from IFC-like records.','risk':'read','requires_approval':False},
    {'name':'iot.telemetry_summary','description':'Aggregate telemetry by point/device.','risk':'read','requires_approval':False},
    {'name':'iot.alarm_scan','description':'Scan telemetry against high/low thresholds.','risk':'read','requires_approval':False},
    {'name':'water.kpi_summary','description':'Calculate water/wastewater operational KPIs.','risk':'read','requires_approval':False},
    {'name':'water.aeration_advice','description':'Generate advisory-only aeration recommendation from DO samples.','risk':'advisory','requires_approval':False},
    {'name':'project.file_inspect','description':'Inspect Project XML/CSV or route binary MPP to a configured provider adapter.','risk':'read','requires_approval':False},
    {'name':'bim.model_inspect','description':'Inspect IFC with IfcOpenShell when available, otherwise use a STEP fallback parser.','risk':'read','requires_approval':False},
    {'name':'iot.mqtt_readiness','description':'Describe a read-only MQTT telemetry adapter configuration.','risk':'read','requires_approval':False},
    {'name':'iot.tdengine_query','description':'Prepare a read-only TDengine time-series query through a configured adapter.','risk':'read','requires_approval':False},
]

class Call(BaseModel):
    name: str
    arguments: dict = {}

def _schedule(tasks):
    by_id={str(t.get('id')):t for t in tasks}; out=[]
    for t in tasks:
        x=dict(t); start=date.fromisoformat(x['start']); dur=max(1,int(x.get('duration',1)))
        preds=x.get('predecessors') or []
        if isinstance(preds,str): preds=[p.strip() for p in re.split(r'[,;]',preds) if p.strip()]
        finishes=[]
        for p in preds:
            if p in by_id:
                pt=by_id[p]; ps=date.fromisoformat(pt['start']); pd=max(1,int(pt.get('duration',1)))
                finishes.append(ps+timedelta(days=pd-1))
        if finishes: start=max(start,max(finishes)+timedelta(days=1))
        x.update(start=start.isoformat(), finish=(start+timedelta(days=dur-1)).isoformat(), duration=dur, predecessors=preds)
        out.append(x)
    return out

def _project_xml(content):
    import xml.etree.ElementTree as ET
    root=ET.fromstring(content)
    def text(node, name):
        x=node.find('.//{*}'+name)
        return x.text.strip() if x is not None and x.text else None
    tasks=[]
    for n in root.findall('.//{*}Task'):
        uid=text(n,'UID'); name=text(n,'Name') or ''; start=text(n,'Start'); finish=text(n,'Finish')
        tasks.append({'uid':uid,'name':name,'start':start,'finish':finish,'predecessors':[text(p,'ID') for p in n.findall('./{*}PredecessorLink/{*}PredecessorUID') if text(p,'ID')]})
    # Correctly collect predecessor UIDs regardless of namespace layout.
    for n, row in zip(root.findall('.//{*}Task'), tasks):
        row['predecessors']=[x.text.strip() for x in n.findall('./{*}PredecessorLink/{*}PredecessorUID') if x.text]
    return {'task_count':len(tasks),'tasks':tasks[:1000],'dependency_count':sum(len(x['predecessors']) for x in tasks)}

def _ifc_summary(content):
    counts=Counter(m.group(1).upper() for m in re.finditer(r'#\d+\s*=\s*(IFC[A-Z0-9_]+)\s*\(',content,re.I))
    return {'schema':'IFC','total_entities':sum(counts.values()),'entity_counts':dict(counts)}

def _ifc_elements(content, limit=100):
    rows=[]
    for line in content.splitlines():
        m=re.match(r'\s*(#\d+)\s*=\s*([A-Z0-9_]+)\s*\((.*)\)\s*;',line,re.I)
        if m:
            rows.append({'id':m.group(1),'type':m.group(2).upper(),'arguments':m.group(3)[:4000]})
            if len(rows)>=limit: break
    return rows

def _numeric_summary(rows, group_key='point', value_key='value'):
    grouped=defaultdict(list)
    for r in rows:
        v=r.get(value_key); k=r.get(group_key) or r.get('device_id') or 'unknown'
        if isinstance(v,(int,float)): grouped[k].append(float(v))
    return [{'key':k,'count':len(v),'avg':mean(v),'min':min(v),'max':max(v)} for k,v in grouped.items()]

def _alarms(rows, high=None, low=None):
    out=[]
    for r in rows:
        v=r.get('value')
        if not isinstance(v,(int,float)): continue
        if high is not None and v>high: out.append({'point':r.get('point'),'device_id':r.get('device_id'),'value':v,'type':'high'})
        if low is not None and v<low: out.append({'point':r.get('point'),'device_id':r.get('device_id'),'value':v,'type':'low'})
    return out

def _water_kpis(rows):
    keys=['flow','cod','bod','nh3_n','tn','tp','do','mlss','return_sludge_rate']
    result={}
    for k in keys:
        vals=[float(r[k]) for r in rows if isinstance(r.get(k),(int,float))]
        if vals: result[k]={'avg':mean(vals),'min':min(vals),'max':max(vals)}
    return result

def _aeration(rows,target_do=2.0):
    vals=[float(r['do']) for r in rows if isinstance(r.get('do'),(int,float))]
    if not vals: return {'status':'insufficient_data','control_mode':'advisory_only'}
    avg=mean(vals)
    rec='increase_air' if avg<target_do*0.85 else 'decrease_air' if avg>target_do*1.15 else 'hold'
    return {'avg_do':avg,'target_do':target_do,'delta':target_do-avg,'recommendation':rec,'control_mode':'advisory_only'}

def dispatch(name, a):
    if name=='project.schedule_calculate': return {'items':_schedule(a.get('tasks',[]))}
    if name=='project.schedule_variance':
        p=date.fromisoformat(a['planned_finish']); c=date.fromisoformat(a.get('actual_finish') or a.get('today') or date.today().isoformat())
        return {'planned_finish':a['planned_finish'],'comparison_date':c.isoformat(),'variance_days':(c-p).days,'status':'late' if c>p else 'on_track'}
    if name=='project.mpp_xml_summary': return _project_xml(a['content'])
    if name=='bim.ifc_summary': return _ifc_summary(a['content'])
    if name=='bim.ifc_elements': return {'items':_ifc_elements(a['content'],int(a.get('limit',100)))}
    if name=='bim.quantity_summary':
        rows=a.get('elements',[]); vals=[float(x['quantity']) for x in rows if isinstance(x.get('quantity'),(int,float))]
        return {'count':len(vals),'total_quantity':sum(vals),'avg_quantity':mean(vals) if vals else None}
    if name=='iot.telemetry_summary': return {'items':_numeric_summary(a.get('points',[]))}
    if name=='iot.alarm_scan': return {'items':_alarms(a.get('points',[]),a.get('high'),a.get('low'))}
    if name=='water.kpi_summary': return {'kpis':_water_kpis(a.get('samples',[]))}
    if name=='water.aeration_advice': return _aeration(a.get('samples',[]),float(a.get('target_do',2.0)))
    if name=='project.file_inspect': return project_connector.inspect(a['filename'],a['content'])
    if name=='bim.model_inspect': return bim_connector.inspect(a['content'],int(a.get('limit',500)))
    if name=='iot.mqtt_readiness': return {'provider':'mqtt','broker':a['broker'],'topic':a['topic'],'mode':'read_only','status':'adapter_ready'}
    if name=='iot.tdengine_query': return {'provider':'tdengine','dsn':a.get('dsn'),'sql':a['sql'],'mode':'read_only','status':'adapter_ready','rows':[]}
    raise KeyError(name)

@app.get('/health')
async def health(): return {'status':'ok','version':'3.9.0','tools':len(TOOLS)}
@app.get('/tools')
async def tools(): return {'tools':TOOLS}
@app.post('/call')
async def call(c:Call):
    try: return {'name':c.name,'result':dispatch(c.name,c.arguments)}
    except KeyError: raise HTTPException(404,'tool_not_found')
    except Exception as e: raise HTTPException(400,f'connector_error: {e}')
