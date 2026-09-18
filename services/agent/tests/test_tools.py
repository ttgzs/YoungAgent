import asyncio
from app.tools import ToolRegistry, Tool

def test_registry():
    r=ToolRegistry(); r.register(Tool('x','x',lambda:1)); assert r.get('x').name=='x'

def test_python_sandbox():
    from app.tools import python_sandbox
    out=asyncio.run(python_sandbox('print(2+3)')); assert '5' in out['stdout']
