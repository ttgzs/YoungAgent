import json
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, JSON, select
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, Session
class Checkpoint(Base):
    __tablename__='agent_checkpoints'
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True); task_id:Mapped[str]=mapped_column(String(64),index=True); step:Mapped[int]=mapped_column(default=0); state:Mapped[dict]=mapped_column(JSON); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
async def save_checkpoint(task_id,step,state):
    async with Session() as s: s.add(Checkpoint(task_id=task_id,step=step,state=state)); await s.commit()
async def latest_checkpoint(task_id):
    async with Session() as s:
        r=await s.execute(select(Checkpoint).where(Checkpoint.task_id==task_id).order_by(Checkpoint.step.desc()).limit(1)); x=r.scalar_one_or_none(); return None if not x else {'step':x.step,'state':x.state}
