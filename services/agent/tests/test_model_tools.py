import asyncio
from app.runtime import AgentRuntime
from app.model import ModelGateway

def test_tool_schema():
    rt=AgentRuntime(); names=[x['function']['name'] for x in rt.tool_schemas()]
    assert 'filesystem.read' in names and 'python.sandbox' in names

def test_model_gateway_without_config():
    async def run():
        r=await ModelGateway().chat([{'role':'user','content':'hi'}])
        assert r['tool_calls']==[]
        assert '未配置' in r['content']
    asyncio.run(run())
