import json, uuid
from avito_ai_combine.automation.policies import AutonomyMode, PolicyEngine, KillSwitch
class AutopilotService:
    def __init__(self,runtime,kill_switch=None,spend_limit=0): self.rt=runtime; self.kill_switch=kill_switch or KillSwitch(); self.spend_limit=spend_limit
    def propose(self,event,payload):
        if event=='lead.score.changed' and float(payload.get('score',0))>=70: return [{'type':'create_task','lead_id':payload.get('lead_id'),'title':'Связаться с горячим лидом'}]
        if event=='listing.performance.low': return [{'type':'promotion_review','item_id':payload.get('item_id'),'amount':float(payload.get('promotion_amount',0) or 0)}]
        if event=='review.new': return [{'type':'draft_review_reply','review_id':payload.get('review_id')}]
        return []
    def process(self,event,payload):
        actions=self.propose(event,payload); mode=AutonomyMode(self.rt.config.autonomy_mode)
        if not actions: return {'status':'no_action','actions':[]}
        if mode in (AutonomyMode.OFF,AutonomyMode.ADVISER): return {'status':'advice','actions':actions}
        if mode==AutonomyMode.COPILOT: return {'status':'approval','actions':actions}
        for a in actions:
            monetary=a['type']=='promotion_review'; decision=PolicyEngine(mode,self.kill_switch,self.spend_limit).authorize(a['type'],monetary=monetary,amount=a.get('amount',0))
            if not decision.allowed: return {'status':'approval' if decision.requires_approval else 'blocked','reason':decision.reason,'actions':actions}
            if a['type']=='create_task': self.rt.db.execute('insert into lead_tasks(external_id,account_id,data) values(?,?,?)',(str(uuid.uuid4()),str(self.rt.account_id),json.dumps(a,ensure_ascii=False)))
        self.rt.db.execute('insert into ai_runs(external_id,account_id,data) values(?,?,?)',(str(uuid.uuid4()),str(self.rt.account_id),json.dumps({'event':event,'actions':actions,'mode':mode.value},ensure_ascii=False)))
        return {'status':'executed','actions':actions}
