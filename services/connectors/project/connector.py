from __future__ import annotations
import csv, io, xml.etree.ElementTree as ET

class ProjectConnector:
    def from_project_xml(self, content: str) -> dict:
        root=ET.fromstring(content)
        tasks=[]
        for n in root.findall('.//{*}Task'):
            def t(name):
                x=n.find('./{*}'+name)
                return x.text.strip() if x is not None and x.text else None
            uid=t('UID'); name=t('Name') or ''
            preds=[x.text.strip() for x in n.findall('./{*}PredecessorLink/{*}PredecessorUID') if x.text]
            tasks.append({'uid':uid,'name':name,'start':t('Start'),'finish':t('Finish'),'predecessors':preds})
        return {'format':'project_xml','task_count':len(tasks),'tasks':tasks}
    def from_csv(self, content: str) -> dict:
        rows=list(csv.DictReader(io.StringIO(content)))
        return {'format':'csv','task_count':len(rows),'tasks':rows}
    def inspect(self, filename: str, content: str) -> dict:
        ext=filename.lower().rsplit('.',1)[-1] if '.' in filename else ''
        if ext in ('xml','mppxml'): return self.from_project_xml(content)
        if ext=='csv': return self.from_csv(content)
        if ext=='mpp':
            return {'format':'mpp_adapter_required','supported_adapters':['project_xml_export','project_server','commercial_mpp_sdk'],'message':'Binary MPP requires an installed provider adapter; do not pretend to parse it as text.'}
        raise ValueError('unsupported_project_format')
