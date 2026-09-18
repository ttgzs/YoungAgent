from __future__ import annotations
import re
class BIMConnector:
    def inspect(self, content: str, limit=500):
        try:
            import ifcopenshell
            model=ifcopenshell.file.from_string(content)
            ents=model.by_type('IfcProduct')
            return {'provider':'ifcopenshell','product_count':len(ents),'items':[{'id':e.id(),'type':e.is_a(),'name':getattr(e,'Name',None)} for e in ents[:limit]]}
        except Exception:
            rows=[]
            for m in re.finditer(r'#(\d+)\s*=\s*(IFC[A-Z0-9_]+)\s*\((.*)\);',content,re.I):
                rows.append({'id':int(m.group(1)),'type':m.group(2).upper(),'raw':m.group(3)[:1000]})
                if len(rows)>=limit: break
            return {'provider':'step-fallback','product_count':len(rows),'items':rows}
