from dataclasses import dataclass
import httpx
@dataclass
class MCPServer: name:str; url:str; tenant_id:str='*'; enabled:bool=True
class MCPRegistry:
    def __init__(self): self.servers={}
    def register(self,s): self.servers[s.name]=s
    def list(self,tenant_id): return [s for s in self.servers.values() if s.enabled and (s.tenant_id in ('*',tenant_id))]
    async def call(self,server,method,params,tenant_id):
        s=self.servers[server]
        if s.tenant_id not in ('*',tenant_id): raise PermissionError('MCP租户无权访问')
        async with httpx.AsyncClient(timeout=60) as c:
            r=await c.post(s.url.rstrip('/')+'/call',json={'method':method,'params':params,'tenant_id':tenant_id}); r.raise_for_status(); return r.json()
