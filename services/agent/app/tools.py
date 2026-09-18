from dataclasses import dataclass
from typing import Callable, Dict, Any
import os, json, subprocess, tempfile

@dataclass
class Tool:
    name: str; description: str; handler: Callable[..., Any]; risk: str='read'
    requires_approval: bool=False

class ToolRegistry:
    def __init__(self): self._tools: Dict[str,Tool]={}
    def register(self, tool): self._tools[tool.name]=tool
    def list(self): return list(self._tools.values())
    def get(self,name): return self._tools.get(name)

async def fs_read(path: str):
    path=os.path.abspath(path); return {'path':path,'content':open(path,encoding='utf-8').read()}
async def fs_list(path: str='.'): return {'path':os.path.abspath(path),'items':os.listdir(path)}
async def python_sandbox(code: str):
    with tempfile.TemporaryDirectory() as d:
        p=os.path.join(d,'main.py'); open(p,'w',encoding='utf-8').write(code)
        r=subprocess.run(['python',p],capture_output=True,text=True,timeout=15,cwd=d)
        return {'returncode':r.returncode,'stdout':r.stdout[-8000:],'stderr':r.stderr[-8000:]}

async def knowledge_search(query: str):
    from .rag import search_documents
    return await search_documents('default',query)
