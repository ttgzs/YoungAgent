from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class Principal:
    user_id:str='anonymous'; tenant_id:str='default'; roles:tuple[str,...]=('user',)

ROLE_PERMS={'user':{'task.run','tool.read'},'operator':{'task.run','tool.read','tool.write','approval.request'},'admin':{'task.run','tool.read','tool.write','approval.request','admin.manage'}}

def allowed(principal:Principal, permission:str)->bool:
    return any(permission in ROLE_PERMS.get(r,set()) for r in principal.roles)

class AuditLog:
    def __init__(self): self.items=[]
    def record(self, action, principal, resource, outcome, meta=None):
        self.items.append({'ts':datetime.now(timezone.utc).isoformat(),'action':action,'user_id':principal.user_id,'tenant_id':principal.tenant_id,'resource':resource,'outcome':outcome,'meta':meta or {}})
    def list(self, tenant_id=None):
        return [x for x in self.items if tenant_id is None or x['tenant_id']==tenant_id]
