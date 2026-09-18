from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, JSON, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .config import settings

class Base(DeclarativeBase): pass

class Task(Base):
    __tablename__='agent_tasks'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, default='default')
    user_id: Mapped[str] = mapped_column(String(128), index=True, default='anonymous')
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True, default='running')
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Event(Base):
    __tablename__='agent_events'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, default='default')
    type: Mapped[str] = mapped_column(String(64), index=True)
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

engine=create_async_engine(settings.database_url, future=True)
Session=async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)

async def save_event(task_id, typ, data, tenant_id='default'):
    async with Session() as s:
        s.add(Event(task_id=task_id, tenant_id=tenant_id, type=typ, data=data)); await s.commit()

async def save_task(task_id,prompt,status,result=None,tenant_id='default',user_id='anonymous'):
    async with Session() as s:
        obj=await s.get(Task, task_id)
        if obj is None:
            obj=Task(id=task_id,prompt=prompt,status=status,result=result,tenant_id=tenant_id,user_id=user_id); s.add(obj)
        else:
            obj.status=status; obj.result=result; obj.updated_at=datetime.now(timezone.utc)
        await s.commit()

async def get_task(task_id, tenant_id):
    async with Session() as s:
        r=await s.execute(select(Task).where(Task.id==task_id, Task.tenant_id==tenant_id)); obj=r.scalar_one_or_none()
        return None if obj is None else {'id':obj.id,'tenant_id':obj.tenant_id,'user_id':obj.user_id,'prompt':obj.prompt,'status':obj.status,'result':obj.result,'created_at':obj.created_at.isoformat(),'updated_at':obj.updated_at.isoformat()}

async def get_events(task_id, tenant_id):
    async with Session() as s:
        r=await s.execute(select(Event).where(Event.task_id==task_id, Event.tenant_id==tenant_id).order_by(Event.id));
        return [{'id':e.id,'task_id':e.task_id,'type':e.type,'data':e.data,'created_at':e.created_at.isoformat()} for e in r.scalars().all()]

