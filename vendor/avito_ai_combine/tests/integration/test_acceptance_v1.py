from pathlib import Path
from avito_ai_combine.webhooks.handlers import WebhookIngestor
from avito_ai_combine.services.messaging import MessagingService
from avito_ai_combine.automation.policies import PolicyEngine,AutonomyMode,KillSwitch
from avito_ai_combine.services.promotion_service import PromotionService
from avito_ai_combine.services.diagnostics import DiagnosticsService
from avito_ai_combine.ui.navigation import PAGES
class Msg:
    def __init__(self): self.n=0
    def send_text(self,*a): self.n+=1; return {'id':'m1'}
class Promo:
    def __init__(self): self.n=0
    def create_order(self,*a): self.n+=1; return {'id':'o1'}
def test_webhook_and_send_idempotency():
    w=WebhookIngestor(); p={'id':'e1','message':'x'}
    assert not w.ingest(p)['duplicate']; assert w.ingest(p)['duplicate']; assert len(w.events)==1
    c=Msg(); s=MessagingService(c); assert s.send_text('c','x','k')==s.send_text('c','x','k'); assert c.n==1
def test_promotion_policy_and_kill_switch():
    p=Promo(); k=KillSwitch(); policy=PolicyEngine(AutonomyMode.AUTOPILOT,k,spend_limit=1000); s=PromotionService(p,policy)
    assert s.execute({},'x',1500)['status']=='approval'; assert p.n==0
    k.activate(); assert s.execute({},'y',500)['status']=='blocked'; assert p.n==0
def test_redacted_bundle(tmp_path):
    f=tmp_path/'d.json'; DiagnosticsService({'access_token':'secret','phone':'+79990001122','api':'ok'}).export_redacted_bundle(f); t=f.read_text(); assert 'secret' not in t and '79990001122' not in t
def test_ui_has_fourteen_avito_pages(): assert len(PAGES)==14 and 'Messages' in PAGES and 'Automation' in PAGES
