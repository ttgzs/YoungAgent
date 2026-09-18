from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import uuid

@dataclass
class AgentDefinition:
    id:str; tenant_id:str; name:str; description:str; model:str=''; system_prompt:str=''; enabled:bool=True; created_at:str=''

class AgentCatalog:
    def __init__(self): self.items={}
    def create(self,tenant_id,name,description='',model='',system_prompt=''):
        aid=uuid.uuid4().hex[:16]; obj=AgentDefinition(aid,tenant_id,name,description,model,system_prompt,True,datetime.now(timezone.utc).isoformat()); self.items[aid]=obj; return asdict(obj)
    def list(self,tenant_id): return [asdict(x) for x in self.items.values() if x.tenant_id==tenant_id]
    def get(self,aid,tenant_id):
        x=self.items.get(aid); return asdict(x) if x and x.tenant_id==tenant_id else None
    def delete(self,aid,tenant_id):
        x=self.items.get(aid)
        if not x or x.tenant_id!=tenant_id:return False
        del self.items[aid]; return True

catalog=AgentCatalog()
