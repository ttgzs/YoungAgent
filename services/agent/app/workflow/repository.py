from sqlalchemy import String, Text, DateTime, JSON, select
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from ..db import Base, Session
class WorkflowRecord(Base):
    __tablename__='agent_workflows'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    tenant_id:Mapped[str]=mapped_column(String(128),index=True,default='default')
    name:Mapped[str]=mapped_column(String(200)); status:Mapped[str]=mapped_column(String(32),index=True)
    payload:Mapped[dict]=mapped_column(JSON); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc)); updated_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
async def save_workflow(payload,tenant_id='default'):
    async with Session() as s:
        obj=await s.get(WorkflowRecord,payload['id'])
        if obj is None: obj=WorkflowRecord(id=payload['id'],tenant_id=tenant_id,name=payload['name'],status=payload['status'],payload=payload); s.add(obj)
        else: obj.name=payload['name']; obj.status=payload['status']; obj.payload=payload; obj.updated_at=datetime.now(timezone.utc)
        await s.commit()
async def load_workflow(wid,tenant_id='default'):
    async with Session() as s:
        r=await s.execute(select(WorkflowRecord).where(WorkflowRecord.id==wid,WorkflowRecord.tenant_id==tenant_id)); o=r.scalar_one_or_none(); return o.payload if o else None
async def list_workflows(tenant_id='default'):
    async with Session() as s:
        r=await s.execute(select(WorkflowRecord).where(WorkflowRecord.tenant_id==tenant_id).order_by(WorkflowRecord.updated_at.desc())); return [o.payload for o in r.scalars().all()]
