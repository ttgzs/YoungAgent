from __future__ import annotations
import asyncio, uuid
from dataclasses import dataclass, field
from typing import Awaitable, Callable

@dataclass
class WorkPackage:
    id: str
    title: str
    prompt: str
    deps: list[str] = field(default_factory=list)
    agent_type: str = 'general'

@dataclass
class WorkResult:
    id: str
    status: str
    output: str = ''
    error: str | None = None

class AgentOrchestrator:
    """DAG executor: independent work packages run concurrently; dependent packages wait."""
    def __init__(self, runner: Callable[[str, str], Awaitable[str]]): self.runner=runner
    async def run(self, packages:list[WorkPackage], emit=None):
        by_id={p.id:p for p in packages}; done={}; pending=set(by_id)
        async def event(t,d):
            if emit: await emit(t,d)
        while pending:
            ready=[by_id[i] for i in pending if all(d in done for d in by_id[i].deps)]
            if not ready: raise ValueError('工作包存在循环依赖或未知依赖')
            await event('parallel.start',{'packages':[p.id for p in ready]})
            async def one(p):
                try:
                    context='\n'.join(f"{d}: {done[d].output}" for d in p.deps)
                    prompt=p.prompt + ('\n依赖结果：\n'+context if context else '')
                    output=await self.runner(p.agent_type,prompt)
                    return WorkResult(p.id,'completed',output)
                except Exception as e: return WorkResult(p.id,'failed',error=str(e))
            results=await asyncio.gather(*(one(p) for p in ready))
            for r in results: done[r.id]=r; pending.remove(r.id); await event('subagent.finish',{'id':r.id,'status':r.status,'output':r.output,'error':r.error})
            if any(r.status=='failed' for r in results): break
        return {k:v.__dict__ for k,v in done.items()}

def default_packages(task:str):
    return [
      WorkPackage('research','资料/数据分析',f'分析任务并列出关键事实、数据和不确定性：{task}',agent_type='research'),
      WorkPackage('execution','执行方案',f'根据任务设计可执行步骤、工具调用和验收条件：{task}',agent_type='planner'),
      WorkPackage('risk','风险审查',f'审查任务中的权限、安全、数据和业务风险：{task}',agent_type='security'),
      WorkPackage('synthesis','汇总交付',f'综合 research、execution、risk 的结果，形成最终交付：{task}',deps=['research','execution','risk'],agent_type='general')]
