from pathlib import Path
import json
from typing import Any

ROOT = Path(__file__).resolve().parents[3] / 'marketplace' / 'packs'

class Marketplace:
    def __init__(self, root=ROOT):
        self.root=Path(root)
        self.cache={}
        self.reload()
    def reload(self):
        self.cache={}
        for p in self.root.glob('*/manifest.json'):
            try:
                data=json.loads(p.read_text(encoding='utf-8'))
                data['_path']=str(p.parent)
                self.cache[data['id']]=data
            except Exception:
                continue
    def list(self, category=None):
        vals=list(self.cache.values())
        return [self.public(x) for x in vals if not category or x.get('category')==category]
    def get(self, pack_id):
        x=self.cache.get(pack_id)
        return self.public(x) if x else None
    def public(self,x):
        if not x:return None
        y=dict(x); y.pop('_path',None); return y
    def skills(self,pack_id):
        x=self.cache.get(pack_id); return x.get('skills',[]) if x else []
    def install(self,pack_id,tenant_id,installed):
        if pack_id not in self.cache: return None
        installed.setdefault(tenant_id,set()).add(pack_id)
        return {'pack_id':pack_id,'tenant_id':tenant_id,'status':'installed'}
    def installed(self,tenant_id,installed):
        return [self.public(self.cache[x]) for x in installed.get(tenant_id,set()) if x in self.cache]

marketplace=Marketplace()
installed_packs={}
