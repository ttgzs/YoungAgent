from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)
def test_project_xml():
    xml='<Project><Tasks><Task><UID>1</UID><Name>A</Name><Start>2026-01-01</Start><Finish>2026-01-02</Finish></Task></Tasks></Project>'
    r=c.post('/call',json={'name':'project.file_inspect','arguments':{'filename':'x.xml','content':xml}})
    assert r.status_code==200 and r.json()['result']['task_count']==1

def test_bim():
    r=c.post('/call',json={'name':'bim.model_inspect','arguments':{'content':'#1=IFCWALLSTANDARDCASE($,$,$,$);'}})
    assert r.status_code==200 and r.json()['result']['product_count']==1

def test_iot():
    r=c.post('/call',json={'name':'iot.mqtt_readiness','arguments':{'broker':'mqtt://broker','topic':'plant/+/telemetry'}})
    assert r.status_code==200 and r.json()['result']['mode']=='read_only'
