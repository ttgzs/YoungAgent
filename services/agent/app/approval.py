import uuid
class ApprovalGate:
    def __init__(self): self.pending={}
    def request(self, action, payload):
        aid=uuid.uuid4().hex; self.pending[aid]={'action':action,'payload':payload,'status':'pending'}; return aid
    def approve(self, aid):
        if aid in self.pending: self.pending[aid]['status']='approved'
        return self.pending.get(aid)
    def get(self,aid): return self.pending.get(aid)
