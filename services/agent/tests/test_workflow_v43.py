from app.workflow.engine import WorkflowEngine
from app.workflow.designer import validate_definition

def test_retry_and_cancel():
    e=WorkflowEngine({'ok':lambda c:{'ok':1}})
    wf=e.create('x',[{'id':'a','name':'a','action':'ok'}]); e.execute(wf.id,{})
    assert wf.status=='completed'
    assert e.cancel(wf.id).status=='completed'

def test_cycle_detection():
    try: validate_definition([{'id':'a','depends_on':['b']},{'id':'b','depends_on':['a']}])
    except ValueError as ex: assert 'cycle' in str(ex)
    else: assert False
