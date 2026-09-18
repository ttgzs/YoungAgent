"""V3.1-V3.3 domain agent primitives.
Deterministic calculations are intentionally separated from LLM orchestration so they can be audited and tested.
"""
from __future__ import annotations
from datetime import date, timedelta
from statistics import mean
import re


def project_schedule(tasks):
    out=[]; by_id={str(t.get('id')):t for t in tasks}
    for t in tasks:
        x=dict(t); start=date.fromisoformat(x['start']); dur=max(1,int(x.get('duration',1)))
        preds=x.get('predecessors') or []
        if isinstance(preds,str): preds=[p.strip() for p in re.split(r'[,;]',preds) if p.strip()]
        if preds:
            finishes=[]
            for p in preds:
                if p in by_id:
                    pt=by_id[p]; ps=date.fromisoformat(pt['start']); pd=max(1,int(pt.get('duration',1)))
                    finishes.append(ps+timedelta(days=pd-1))
            if finishes: start=max(start,max(finishes)+timedelta(days=1))
        finish=start+timedelta(days=dur-1)
        x.update(start=start.isoformat(),finish=finish.isoformat(),duration=dur,predecessors=preds)
        out.append(x)
    return out


def schedule_variance(planned_finish, actual_finish=None, today=None):
    p=date.fromisoformat(planned_finish); a=date.fromisoformat(actual_finish) if actual_finish else date.fromisoformat(today) if today else date.today()
    return {'planned_finish':planned_finish,'comparison_date':a.isoformat(),'variance_days':(a-p).days,'status':'late' if a>p else 'on_track'}


def parse_ifc_summary(content:str):
    counts={}
    for m in re.finditer(r'#\d+\s*=\s*(IFC[A-Z0-9_]+)\s*\(',content,re.I):
        k=m.group(1).upper(); counts[k]=counts.get(k,0)+1
    return {'entity_counts':counts,'total_entities':sum(counts.values()),'schema': 'IFC'}


def extract_ifc_properties(content:str, limit=100):
    rows=[]
    for line in content.splitlines():
        m=re.match(r'\s*(#\d+)\s*=\s*([A-Z0-9_]+)\s*\((.*)\)\s*;',line,re.I)
        if m:
            rows.append({'id':m.group(1),'type':m.group(2).upper(),'arguments':m.group(3)[:2000]})
            if len(rows)>=limit: break
    return rows


def water_kpis(samples):
    numeric={}
    for row in samples:
        for k,v in row.items():
            if isinstance(v,(int,float)): numeric.setdefault(k,[]).append(float(v))
    return {k:{'avg':mean(v),'min':min(v),'max':max(v)} for k,v in numeric.items() if v}


def aeration_recommendation(samples, target_do=2.0):
    if not samples: return {'status':'insufficient_data'}
    dos=[float(x['do']) for x in samples if 'do' in x]
    if not dos:return {'status':'insufficient_data'}
    avg=mean(dos); delta=target_do-avg
    if avg < target_do*0.85: action='increase_air'
    elif avg > target_do*1.15: action='decrease_air'
    else: action='hold'
    return {'avg_do':avg,'target_do':target_do,'delta':delta,'recommendation':action,'control_mode':'advisory_only'}


def telemetry_summary(points):
    grouped={}
    for p in points:
        name=p.get('point') or p.get('device_id') or 'unknown'; v=p.get('value')
        if isinstance(v,(int,float)): grouped.setdefault(name,[]).append(float(v))
    return [{'point':k,'count':len(v),'avg':mean(v),'min':min(v),'max':max(v)} for k,v in grouped.items()]


def alarm_rules(points, high=None, low=None):
    alarms=[]
    for p in points:
        v=p.get('value');
        if not isinstance(v,(int,float)): continue
        if high is not None and v>high: alarms.append({'point':p.get('point'),'value':v,'type':'high'})
        if low is not None and v<low: alarms.append({'point':p.get('point'),'value':v,'type':'low'})
    return alarms
