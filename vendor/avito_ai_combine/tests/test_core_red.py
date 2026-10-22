from pathlib import Path
import tempfile, sqlite3

def test_foundation_contracts():
    from avito_ai_combine.storage.db import Database
    from avito_ai_combine.storage.migrations import MigrationRunner
    from avito_ai_combine.security.redaction import redact_mapping
    with tempfile.TemporaryDirectory() as d:
        db=Database(Path(d)/'a.db'); assert MigrationRunner.apply(db)>=1
        assert 'leads' in db.table_names()
    x=redact_mapping({'Authorization':'Bearer secret','phone':'+79990001122','ok':'x'})
    assert 'secret' not in str(x) and '79990001122' not in str(x)

def test_retry_and_transport_errors():
    from avito_ai_combine.jobs.retry import RetryPolicy
    from avito_ai_combine.app.exceptions import RateLimitError, ValidationError
    assert RetryPolicy().next_delay(RateLimitError('x'),2)>0
    assert RetryPolicy().next_delay(ValidationError('x'),2) is None

def test_lead_scoring_reasons():
    from avito_ai_combine.crm.scoring import LeadScorer
    s=LeadScorer().score({'intent_strength':1,'contact_language':True,'spam':False})
    assert s.value>0 and 'intent_strength' in s.reason_codes

def test_policy_kill_switch():
    from avito_ai_combine.automation.policies import PolicyEngine, AutonomyMode, KillSwitch
    k=KillSwitch(); k.activate()
    d=PolicyEngine(AutonomyMode.AUTOPILOT,k).authorize('send_message', monetary=False)
    assert not d.allowed and d.reason=='kill_switch'

def test_metrics_zero_safe():
    from avito_ai_combine.analytics.metrics import MetricsCalculator
    m=MetricsCalculator.calculate({'views':0,'contacts':0,'spend':0})
    assert m['contact_rate'] is None
