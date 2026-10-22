from avito_ai_combine.app.bootstrap import build_local_runtime
from avito_ai_combine.services.rule_engine import PersistentRuleEngine
from avito_ai_combine.automation.policies import AutonomyMode

def test_rule_dry_run_and_idempotent_execution(tmp_path):
    rt=build_local_runtime(tmp_path)
    eng=PersistentRuleEngine(rt)
    rid=eng.create_rule('hot lead', 'lead.score.changed', {'min_score':70}, {'type':'create_task','title':'Связаться'}, AutonomyMode.AUTOPILOT)
    dry=eng.handle('e1','lead.score.changed',{'lead_id':'L1','score':80},dry_run=True)
    assert dry[0]['status']=='would_execute'
    assert rt.db.scalar('select count(*) from lead_tasks') == 0
    first=eng.handle('e1','lead.score.changed',{'lead_id':'L1','score':80})
    second=eng.handle('e1','lead.score.changed',{'lead_id':'L1','score':80})
    assert first[0]['status']=='executed'
    assert second[0]['status']=='duplicate'
    assert rt.db.scalar('select count(*) from lead_tasks') == 1
