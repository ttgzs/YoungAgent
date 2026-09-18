from app.workflow.engine import WorkflowEngine

def test_dag_and_approval():
    e=WorkflowEngine({'read':lambda c:{'ok':1},'write':lambda c:{'written':1}})
    w=e.create('x',[{'id':'a','name':'read','action':'read'},{'id':'b','name':'write','action':'write','depends_on':['a'],'requires_approval':True}])
    w=e.execute(w.id,{})
    assert w.status=='awaiting_approval' and w.steps['a'].status=='completed'
    w=e.approve_and_resume(w.id,'b',{})
    assert w.status=='completed'
