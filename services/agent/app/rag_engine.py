import hashlib, math, re, json, httpx
from sqlalchemy import String, Text, Integer, select
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, Session
from .config import settings

class KnowledgeChunk(Base):
    __tablename__='knowledge_chunks'
    id: Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str]=mapped_column(String(128), index=True)
    document_id: Mapped[int]=mapped_column(Integer, index=True)
    title: Mapped[str]=mapped_column(String(300))
    content: Mapped[str]=mapped_column(Text)
    embedding: Mapped[str]=mapped_column(Text)

def chunks(text, size=800, overlap=120):
    text=re.sub(r'\s+',' ',text).strip(); out=[]; start=0
    while start < len(text):
        end=min(len(text), start+size); out.append(text[start:end])
        if end==len(text): break
        start=max(0,end-overlap)
    return out

def local_embedding(text, dims=96):
    v=[0.0]*dims
    for token in re.findall(r'[\w\u4e00-\u9fff]+', text.lower()):
        h=hashlib.sha256(token.encode()).digest()
        for i,b in enumerate(h[:8]): v[(b+i*13)%dims]+=1.0
    n=math.sqrt(sum(x*x for x in v)) or 1.0
    return [round(x/n,7) for x in v]

async def embedding(text):
    if not settings.embedding_model or not settings.api_key:
        return local_embedding(text)
    url=settings.base_url.rstrip('/')+'/embeddings'
    payload={'model':settings.embedding_model,'input':text}
    headers={'Authorization':f'Bearer {settings.api_key}'}
    async with httpx.AsyncClient(timeout=settings.model_timeout_seconds) as c:
        r=await c.post(url,json=payload,headers=headers); r.raise_for_status()
        return r.json()['data'][0]['embedding']

def cosine(a,b):
    if not a or not b: return 0.0
    dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b))
    return dot/(na*nb) if na and nb else 0.0

async def index_document(tenant_id, document_id, title, content):
    parts=chunks(content)
    async with Session() as s:
        for part in parts:
            s.add(KnowledgeChunk(tenant_id=tenant_id,document_id=document_id,title=title,content=part,embedding=json.dumps(await embedding(part))))
        await s.commit()

async def semantic_search(tenant_id, query, limit=5):
    q=await embedding(query)
    async with Session() as s:
        r=await s.execute(select(KnowledgeChunk).where(KnowledgeChunk.tenant_id==tenant_id))
        rows=r.scalars().all()
    scored=[]
    for row in rows:
        try: score=cosine(q,json.loads(row.embedding))
        except Exception: score=0.0
        scored.append((score,row))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [{'id':r.id,'document_id':r.document_id,'title':r.title,'content':r.content,'score':round(score,5)} for score,r in scored[:limit]]
