import re
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base,Session
class Document(Base):
    __tablename__='knowledge_documents'; id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True); tenant_id:Mapped[str]=mapped_column(String(128),index=True); title:Mapped[str]=mapped_column(String(300)); content:Mapped[str]=mapped_column(Text)
async def add_document(tenant_id,title,content):
    async with Session() as s: s.add(Document(tenant_id=tenant_id,title=title,content=content)); await s.commit()
async def search_documents(tenant_id,q,limit=5):
    async with Session() as s:
        r=await s.execute(select(Document).where(Document.tenant_id==tenant_id)); docs=r.scalars().all()
    terms=[x.lower() for x in re.findall(r'\w+',q)]; scored=[]
    for d in docs:
        text=(d.title+' '+d.content).lower(); score=sum(text.count(t) for t in terms); 
        if score: scored.append((score,d))
    scored.sort(key=lambda x:x[0],reverse=True); return [{'id':d.id,'title':d.title,'content':d.content,'score':score} for score,d in scored[:limit]]
