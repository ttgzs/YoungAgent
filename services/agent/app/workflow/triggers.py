from __future__ import annotations
import asyncio, json, time, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class Trigger:
    id: str
    workflow_id: str
    kind: str
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_fired_at: str | None = None

class TriggerRegistry:
    def __init__(self): self.items: dict[str, Trigger] = {}
    def create(self, workflow_id, kind, config):
        if kind not in ('event','interval','cron','webhook'): raise ValueError('unsupported_trigger')
        t=Trigger(uuid.uuid4().hex,workflow_id,kind,config)
        self.items[t.id]=t; return t
    def list(self, workflow_id=None): return [t for t in self.items.values() if workflow_id is None or t.workflow_id==workflow_id]
    def delete(self, tid): return self.items.pop(tid,None)
    def due(self, now=None):
        now=now or time.time(); out=[]
        for t in self.items.values():
            if not t.enabled or t.kind!='interval': continue
            interval=max(1,int(t.config.get('seconds',60)))
            last=time.mktime(datetime.fromisoformat(t.last_fired_at).timetuple()) if t.last_fired_at else 0
            if now-last>=interval: out.append(t)
        return out
    def fired(self,t): t.last_fired_at=datetime.now(timezone.utc).isoformat()
    def serialize(self,t): return t.__dict__.copy()

class EventBus:
    def __init__(self): self.subscribers: dict[str,list] = {}
    def subscribe(self,event_type,callback): self.subscribers.setdefault(event_type,[]).append(callback)
    async def publish(self,event_type,payload):
        results=[]
        for cb in self.subscribers.get(event_type,[]):
            result=cb(payload)
            if asyncio.iscoroutine(result): result=await result
            results.append(result)
        return results
