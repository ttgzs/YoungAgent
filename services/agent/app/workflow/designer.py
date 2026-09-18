"""Workflow Designer schema/validation used by Vue/Electron visual editor."""
from collections import defaultdict, deque

def validate_definition(steps):
    ids=[s.get('id') for s in steps]
    if any(not x for x in ids) or len(set(ids))!=len(ids): raise ValueError('invalid_or_duplicate_step_id')
    known=set(ids)
    for s in steps:
        deps=s.get('depends_on',[])
        if any(d not in known for d in deps): raise ValueError(f"unknown_dependency:{s['id']}")
    indeg={x:0 for x in ids}; graph=defaultdict(list)
    for s in steps:
        for d in s.get('depends_on',[]): indeg[s['id']]+=1; graph[d].append(s['id'])
    q=deque([x for x,v in indeg.items() if v==0]); seen=0
    while q:
        x=q.popleft(); seen+=1
        for y in graph[x]: indeg[y]-=1; q.append(y) if indeg[y]==0 else None
    if seen!=len(ids): raise ValueError('workflow_cycle_detected')
    return {'valid':True,'steps':len(ids),'roots':[x for x,v in {x:sum(x in s.get('depends_on',[]) for s in steps) for x in ids}.items() if v==0]}

def template(name):
    templates={
      'project_progress': [('read_project','读取项目计划','project.schedule',[],False),('variance','分析进度偏差','project.variance',['read_project'],False),('change','生成Gantt变更集','project.gantt.writeback',['variance'],True)],
      'bim_issue': [('model','读取IFC模型','bim.ifc.summary',[],False),('issue','创建BIM问题单','bim.issue.create',['model'],True)],
      'iot_alarm': [('telemetry','读取遥测','iot.telemetry',[],False),('workorder','创建工单','iot.work_order.create',['telemetry'],True)]}
    if name not in templates: raise KeyError(name)
    return [{'id':a,'name':b,'action':c,'depends_on':d,'requires_approval':e} for a,b,c,d,e in templates[name]]
