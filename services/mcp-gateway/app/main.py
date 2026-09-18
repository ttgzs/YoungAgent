import os, httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
app=FastAPI(title='Enterprise MCP Gateway',version='3.6.0')
TOOLS={}
DOMAIN_MCP_URL=os.getenv('DOMAIN_MCP_URL','http://domain-mcp:8110')
class Call(BaseModel): name:str; arguments:dict={}
@app.get('/health')
async def health(): return {'status':'ok','servers':1,'domain_mcp':DOMAIN_MCP_URL}
@app.get('/tools')
async def tools():
    local=list(TOOLS.values())
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r=await c.get(DOMAIN_MCP_URL+'/tools'); r.raise_for_status(); return {'tools':local+r.json().get('tools',[])}
    except Exception:
        return {'tools':local}
@app.post('/call')
async def call(c:Call):
    if c.name in TOOLS:
        return {'name':c.name,'result':{'status':'adapter_placeholder','arguments':c.arguments}}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r=await client.post(DOMAIN_MCP_URL+'/call',json={'name':c.name,'arguments':c.arguments});
            if r.status_code==404: raise HTTPException(404,'tool_not_found')
            r.raise_for_status(); return r.json()
    except HTTPException: raise
    except Exception as e: raise HTTPException(502,f'domain_mcp_unavailable: {e}')
