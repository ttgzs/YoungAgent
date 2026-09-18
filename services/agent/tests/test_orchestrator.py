import asyncio
from app.orchestrator import AgentOrchestrator, WorkPackage

def test_parallel_dag():
    seen=[]
    async def runner(kind,prompt): seen.append(kind); await asyncio.sleep(0.01); return kind+' ok'
    async def go():
        ps=[WorkPackage('a','A','a'),WorkPackage('b','B','b'),WorkPackage('c','C','c',deps=['a','b'])]
        r=await AgentOrchestrator(runner).run(ps); assert set(r)=={'a','b','c'}; assert r['c']['status']=='completed'
    asyncio.run(go())
