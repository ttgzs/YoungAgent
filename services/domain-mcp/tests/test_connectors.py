import sys
sys.path.insert(0,'../')
from app.main import dispatch

def test_project_schedule():
    r=dispatch('project.schedule_calculate',{'tasks':[{'id':'1','start':'2026-01-01','duration':2},{'id':'2','start':'2026-01-01','duration':3,'predecessors':['1']}]})
    assert r['items'][1]['start']=='2026-01-03'

def test_ifc_summary():
    r=dispatch('bim.ifc_summary',{'content':'#1=IFCWALL();\n#2=IFCSLAB();\n#3=IFCWALL();'})
    assert r['total_entities']==3 and r['entity_counts']['IFCWALL']==2

def test_water_advice():
    r=dispatch('water.aeration_advice',{'samples':[{'do':1.0},{'do':1.2}], 'target_do':2.0})
    assert r['recommendation']=='increase_air' and r['control_mode']=='advisory_only'
