import httpx
from .config import settings
class MCPClient:
    async def tools(self):
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r=await c.get(settings.mcp_gateway_url+'/tools'); r.raise_for_status(); return r.json().get('tools',[])
        except Exception:return []
    async def call(self,name,arguments):
        async with httpx.AsyncClient(timeout=120) as c:
            r=await c.post(settings.mcp_gateway_url+'/call',json={'name':name,'arguments':arguments}); r.raise_for_status(); return r.json()
