import asyncio
from .queue import queue
from .runtime import AgentRuntime
from .security import Principal
from .db import save_task,save_event
class AgentWorker:
    def __init__(self): self.runtime=AgentRuntime(); self.running=True
    async def process(self,p):
        principal=Principal(p.get('user_id','anonymous'),p.get('tenant_id','default'),tuple(p.get('roles',['user'])))
        try:
            await save_event(p['task_id'],'worker.started',{'queue':'redis'},principal.tenant_id)
            await self.runtime.run(p['task'],p['task_id'],principal)
        except Exception as e:
            await save_task(p['task_id'],p['task'],'failed',{'error':str(e)},principal.tenant_id,principal.user_id)
            await save_event(p['task_id'],'worker.error',{'error':str(e)},principal.tenant_id)
    async def loop(self):
        while self.running:
            p=await queue.dequeue(3)
            if p: await self.process(p)
async def main(): await AgentWorker().loop()
if __name__=='__main__': asyncio.run(main())
