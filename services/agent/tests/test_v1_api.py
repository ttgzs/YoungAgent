import os, pytest
os.environ['DATABASE_URL']='sqlite+aiosqlite:///./test-v1.db'
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c: yield c

def test_health(client):
    r=client.get('/health'); assert r.status_code==200; assert r.json()['version']=='1.0.1'

def test_empty_task_rejected(client):
    r=client.post('/api/v1/agent/run',json={'task':''}); assert r.status_code==422
