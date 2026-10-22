from avito_ai_combine.app.bootstrap import build_local_runtime
from avito_ai_combine.services.autopilot import AutopilotService
from avito_ai_combine.automation.policies import AutonomyMode

def test_autopilot_advises_then_executes_safe_task_in_autopilot(tmp_path):
    rt=build_local_runtime(tmp_path)
    ap=AutopilotService(rt)
    rt.config.autonomy_mode='ADVISER'
    r=ap.process('lead.score.changed',{'lead_id':'L1','score':85})
    assert r['status']=='advice' and r['actions'][0]['type']=='create_task'
    assert rt.db.scalar('select count(*) from lead_tasks')==0
    rt.config.autonomy_mode='AUTOPILOT'
    r=ap.process('lead.score.changed',{'lead_id':'L1','score':85})
    assert r['status']=='executed'
    assert rt.db.scalar('select count(*) from lead_tasks')==1

def test_autopilot_never_auto_spends_without_positive_limit(tmp_path):
    rt=build_local_runtime(tmp_path); rt.config.autonomy_mode='AUTOPILOT'
    ap=AutopilotService(rt)
    r=ap.process('listing.performance.low',{'item_id':101,'promotion_amount':500})
    assert r['status']=='approval'
    assert rt.db.scalar('select count(*) from promotion_orders')==0
