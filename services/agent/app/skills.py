from pathlib import Path
import re

class Skill:
    def __init__(self,name,description,body,path): self.name=name; self.description=description; self.body=body; self.path=str(path)

class SkillRegistry:
    def __init__(self,root='skills'): self.root=Path(root); self.items={}; self.load()
    def load(self):
        self.items={}
        for p in self.root.glob('*/SKILL.md'):
            body=p.read_text(encoding='utf-8'); name=p.parent.name; m=re.search(r'^description:\s*(.+)$',body,re.M)
            self.items[name]=Skill(name,m.group(1).strip() if m else name,body,p)
    def list(self): return list(self.items.values())
    def get(self,name): return self.items.get(name)
    def prompt(self,names): return '\n\n'.join(self.items[n].body for n in names if n in self.items)
