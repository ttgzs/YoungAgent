import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from app.marketplace import Marketplace

def test_marketplace_catalog():
    m=Marketplace()
    ids={x['id'] for x in m.list()}
    assert {'youngagent.project','youngagent.bim','youngagent.water','youngagent.iot'} <= ids

def test_install_is_tenant_scoped():
    m=Marketplace(); installed={}
    m.install('youngagent.iot','t1',installed)
    assert len(m.installed('t1',installed))==1
    assert m.installed('t2',installed)==[]
