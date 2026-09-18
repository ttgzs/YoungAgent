import json, asyncio
from redis.asyncio import Redis
from .config import settings
class TaskQueue:
    def __init__(self): self.redis=Redis.from_url(settings.redis_url,decode_responses=True)
    async def enqueue(self,payload): await self.redis.rpush(settings.worker_queue,json.dumps(payload,ensure_ascii=False)); return payload['task_id']
    async def dequeue(self,timeout=5):
        item=await self.redis.blpop(settings.worker_queue,timeout=timeout); return None if not item else json.loads(item[1])
    async def close(self): await self.redis.aclose()
queue=TaskQueue()
