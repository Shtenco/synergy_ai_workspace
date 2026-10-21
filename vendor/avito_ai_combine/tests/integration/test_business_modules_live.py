from pathlib import Path
from avito_ai_combine.app.bootstrap import build_local_runtime
from avito_ai_combine.services.business_modules import BusinessModulesService
from avito_ai_combine.automation.policies import AutonomyMode

class FakeTransport:
    def request(self, method, path, **kw):
        if path == '/core/v1/items': return {'resources':[{'id':101,'title':'Visa Spain','status':'active','price':12000}]}
        if path.endswith('/items') and path.startswith('/stats/'): return {'result':{'items':[{'itemId':101,'views':100,'contacts':8,'favorites':4,'spending':500}]}}
        if path == '/ratings/v1/reviews': return {'reviews':[{'id':'r1','score':5,'text':'Отлично'}]}
        if '/calls/stats/' in path: return {'calls':[{'id':'c1','itemId':101,'duration':45}]}
        if path == '/autoload/v4/uploads': return {'uploads':[{'id':'u1','status':'done'}]}
        if path == '/autoload/v4/uploads/current': return {'id':'u1','status':'done'}
        if path == '/promotion/v2/items/services/get': return {'result':[{'itemId':101,'services':[{'id':'x','price':300}]}]}
        if path == '/promotion/v1/items/forecasts/get': return {'result':[{'itemId':101,'forecast':{'views':250}}]}
        raise AssertionError(path)

def test_sync_business_domains_persists_and_dashboard_aggregates(tmp_path):
    rt=build_local_runtime(tmp_path); rt.transport=FakeTransport(); rt.account_id='42'; rt.token=type('T',(),{'access_token':'tok'})()
    svc=BusinessModulesService(rt)
    result=svc.sync_all()
    assert result['listings']==1 and result['stats']==1 and result['reviews']==1 and result['calls']==1
    assert rt.db.scalar('select count(*) from listings') == 1
    assert rt.db.scalar('select count(*) from listing_stats_daily') == 1
    dash=svc.dashboard()
    assert dash['active_listings']==1 and dash['views']==100 and dash['contacts']==8
    assert dash['contact_rate']==0.08

def test_autoload_and_promotion_are_observation_first(tmp_path):
    rt=build_local_runtime(tmp_path); rt.transport=FakeTransport(); rt.account_id='42'; rt.token=type('T',(),{'access_token':'tok'})()
    svc=BusinessModulesService(rt)
    assert svc.autoload_status()['current']['status']=='done'
    promo=svc.promotion_observe([101])
    assert promo['services'] and promo['forecasts']
    # Observation must not create a promotion order.
    assert rt.db.scalar('select count(*) from promotion_orders') == 0
