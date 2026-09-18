from dataclasses import dataclass
import httpx
from .config import settings
@dataclass
class BrowserAdapter:
    base_url:str=settings.browser_service_url
    async def navigate(self,url):
        async with httpx.AsyncClient(timeout=60) as c:
            r=await c.post(self.base_url+'/navigate',json={'url':url}); r.raise_for_status(); return r.json()
    async def snapshot(self,session_id):
        async with httpx.AsyncClient(timeout=60) as c:
            r=await c.get(self.base_url+f'/snapshot/{session_id}'); r.raise_for_status(); return r.json()
    async def click(self,session_id,selector,approved=False):
        async with httpx.AsyncClient(timeout=60) as c:
            r=await c.post(self.base_url+'/click',json={'session_id':session_id,'selector':selector,'approved':approved}); r.raise_for_status(); return r.json()
@dataclass
class ComputerUseAdapter:
    base_url:str='http://computer-use:8091'
    async def snapshot(self,session_id):
        async with httpx.AsyncClient(timeout=60) as c:
            r=await c.get(self.base_url+f'/snapshot/{session_id}'); r.raise_for_status(); return r.json()
    async def action(self,session_id,action,approved=False):
        async with httpx.AsyncClient(timeout=60) as c:
            r=await c.post(self.base_url+'/action',json={'session_id':session_id,'action':action,'approved':approved}); r.raise_for_status(); return r.json()
