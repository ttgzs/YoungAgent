import asyncio
class WorkflowScheduler:
    def __init__(self, registry, fire): self.registry=registry; self.fire=fire; self.running=False
    async def run(self, poll_seconds=2):
        self.running=True
        while self.running:
            for trigger in self.registry.due():
                self.registry.fired(trigger)
                await self.fire(trigger)
            await asyncio.sleep(poll_seconds)
    def stop(self): self.running=False
