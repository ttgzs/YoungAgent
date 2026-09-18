import asyncio, time
import httpx
from .config import settings

class ModelRouter:
    def __init__(self):
        self.providers=[]
        raw=getattr(settings,'model_fallbacks','')
        for item in raw.split(','):
            item=item.strip()
            if item: self.providers.append(item)
        if settings.model_name and settings.model_name not in self.providers: self.providers.insert(0,settings.model_name)
        self.stats={p:{'ok':0,'error':0,'latency_ms':0} for p in self.providers}

    async def chat(self,messages,tools=None):
        last=None
        for model in self.providers or ['']:
            try:
                t=time.perf_counter()
                payload={'model':model,'messages':messages,'temperature':0.2}
                if tools: payload.update({'tools':tools,'tool_choice':'auto'})
                headers={'Authorization':f'Bearer {settings.api_key}','Content-Type':'application/json'}
                async with httpx.AsyncClient(timeout=settings.model_timeout_seconds) as c:
                    r=await c.post(settings.base_url.rstrip('/')+'/chat/completions',json=payload,headers=headers)
                    r.raise_for_status(); data=r.json()
                elapsed=(time.perf_counter()-t)*1000; s=self.stats.setdefault(model,{'ok':0,'error':0,'latency_ms':0}); s['ok']+=1; s['latency_ms']=round((s['latency_ms']*(s['ok']-1)+elapsed)/s['ok'],1)
                msg=data['choices'][0]['message']
                return {'content':msg.get('content') or '','tool_calls':msg.get('tool_calls') or [],'message':msg,'usage':data.get('usage'),'finish_reason':data['choices'][0].get('finish_reason'),'model':model}
            except Exception as e:
                last=e; self.stats.setdefault(model,{'ok':0,'error':0,'latency_ms':0})['error']+=1
                await asyncio.sleep(settings.model_retry_delay_seconds)
        raise RuntimeError(f'所有模型提供商均不可用: {last}')
