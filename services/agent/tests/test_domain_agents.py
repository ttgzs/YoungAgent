from app.domain_agents import project_schedule, parse_ifc_summary, water_kpis, telemetry_summary

def test_project_schedule():
    r=project_schedule([{'id':'1','start':'2026-01-01','duration':2},{'id':'2','start':'2026-01-01','duration':1,'predecessors':['1']}])
    assert r[1]['start']=='2026-01-03'

def test_ifc_summary():
    r=parse_ifc_summary('#1=IFCWALL();\n#2=IFCDOOR();')
    assert r['total_entities']==2

def test_water_kpi():
    assert water_kpis([{'do':1},{'do':3}])['do']['avg']==2

def test_iot():
    assert telemetry_summary([{'point':'p1','value':1},{'point':'p1','value':3}])[0]['avg']==2
