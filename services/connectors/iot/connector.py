from __future__ import annotations
from statistics import mean
class IoTConnector:
    def summarize(self, points):
        grouped={}
        for p in points:
            v=p.get('value')
            if isinstance(v,(int,float)):
                grouped.setdefault(p.get('point') or p.get('device_id') or 'unknown',[]).append(float(v))
        return [{'point':k,'count':len(v),'avg':mean(v),'min':min(v),'max':max(v)} for k,v in grouped.items()]
    async def mqtt_config(self, broker, topic):
        return {'provider':'mqtt','broker':broker,'topic':topic,'mode':'read_only','status':'adapter_ready'}
    async def tdengine_query(self, dsn, sql):
        return {'provider':'tdengine','dsn':dsn,'sql':sql,'mode':'read_only','status':'adapter_ready','rows':[]}
