"""Durable workflow core: DAG, approval, retry/cancel and resumable state."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
import uuid

@dataclass
class Step:
    id: str
    name: str
    action: str
    depends_on: list[str] = field(default_factory=list)
    requires_approval: bool = False
    status: str = 'pending'
    result: Any = None
    attempts: int = 0
    max_attempts: int = 3

@dataclass
class Workflow:
    id: str
    name: str
    steps: dict[str, Step]
    status: str = 'pending'
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    context: dict = field(default_factory=dict)

class WorkflowEngine:
    def __init__(self, handlers=None):
        self.handlers = handlers or {}
        self.workflows: dict[str, Workflow] = {}

    def create(self, name, steps):
        ids={s['id'] for s in steps}
        if len(ids)!=len(steps): raise ValueError('duplicate_step_id')
        for s in steps:
            if any(d not in ids for d in s.get('depends_on', [])): raise ValueError(f"unknown dependency in step {s['id']}")
        wf=Workflow(uuid.uuid4().hex,name,{s['id']:Step(**s) for s in steps})
        self.workflows[wf.id]=wf; return wf

    def restore(self, payload):
        wf=Workflow(payload['id'],payload['name'],{},payload.get('status','pending'),payload.get('created_at',datetime.now(timezone.utc).isoformat()),payload.get('updated_at',datetime.now(timezone.utc).isoformat()),payload.get('context',{}))
        for raw in payload.get('steps',[]):
            raw=dict(raw); raw.pop('_approved',None); wf.steps[raw['id']]=Step(**{k:v for k,v in raw.items() if k in Step.__dataclass_fields__})
        self.workflows[wf.id]=wf; return wf

    def runnable(self,wf):
        return [s for s in wf.steps.values() if s.status=='pending' and all(wf.steps[d].status=='completed' for d in s.depends_on)]

    def execute(self,wf_id,context=None):
        wf=self.workflows[wf_id]; wf.context={**wf.context,**(context or {})}; wf.status='running'; wf.updated_at=datetime.now(timezone.utc).isoformat()
        while True:
            run=self.runnable(wf)
            if not run: break
            for s in run:
                if s.requires_approval and not getattr(s,'_approved',False): s.status='awaiting_approval'; continue
                fn=self.handlers.get(s.action)
                if not fn: s.status='failed'; s.result={'error':'handler_not_found'}; wf.status='failed'; return wf
                try:
                    s.status='running'; s.attempts+=1; s.result=fn({**wf.context,'workflow_id':wf.id,'step_id':s.id}); s.status='completed'; setattr(s,'_approved',False)
                except Exception as e:
                    if s.attempts < s.max_attempts: s.status='pending'; s.result={'error':str(e),'retryable':True}
                    else: s.status='failed'; s.result={'error':str(e),'retryable':False}; wf.status='failed'; return wf
            if any(s.status=='awaiting_approval' for s in wf.steps.values()): wf.status='awaiting_approval'; return wf
        if all(s.status=='completed' for s in wf.steps.values()): wf.status='completed'
        elif any(s.status=='failed' for s in wf.steps.values()): wf.status='failed'
        elif wf.status!='cancelled': wf.status='blocked'
        wf.updated_at=datetime.now(timezone.utc).isoformat(); return wf

    def approve_and_resume(self,wf_id,step_id,context=None):
        wf=self.workflows[wf_id]; step=wf.steps[step_id]
        if step.status!='awaiting_approval': raise ValueError('step_not_awaiting_approval')
        step.status='pending'; setattr(step,'_approved',True); return self.execute(wf_id,context)

    def cancel(self,wf_id):
        wf=self.workflows[wf_id]
        if wf.status in ('completed','failed','cancelled'): return wf
        wf.status='cancelled'
        for s in wf.steps.values():
            if s.status in ('pending','awaiting_approval','running'): s.status='cancelled'
        return wf

    def retry(self,wf_id,step_id=None):
        wf=self.workflows[wf_id]
        targets=[wf.steps[step_id]] if step_id else [s for s in wf.steps.values() if s.status=='failed']
        for s in targets: s.status='pending'; s.result=None
        wf.status='pending'; return wf

    def serialize(self,wf):
        return {'id':wf.id,'name':wf.name,'status':wf.status,'created_at':wf.created_at,'updated_at':wf.updated_at,'context':wf.context,'steps':[s.__dict__.copy() for s in wf.steps.values()]}
