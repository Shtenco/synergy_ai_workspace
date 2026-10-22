import json, uuid
from avito_ai_combine.automation.policies import AutonomyMode, PolicyEngine, KillSwitch
class PersistentRuleEngine:
    def __init__(self,runtime): self.rt=runtime; self.kill_switch=KillSwitch()
    def create_rule(self,name,trigger,conditions,action,mode=AutonomyMode.COPILOT):
        rid=str(uuid.uuid4()); data={'name':name,'trigger':trigger,'conditions':conditions,'action':action,'mode':AutonomyMode(mode).value,'enabled':True}
        self.rt.db.execute('insert into automation_rules(external_id,account_id,data) values(?,?,?)',(rid,str(self.rt.account_id),json.dumps(data,ensure_ascii=False))); return rid
    def _matches(self,conditions,payload):
        if 'min_score' in conditions and float(payload.get('score',0))<float(conditions['min_score']): return False
        return all(payload.get(k)==v for k,v in conditions.items() if k!='min_score')
    def _run_key(self,event_id,rid): return f'{event_id}:{rid}'
    def handle(self,event_id,trigger,payload,dry_run=False):
        out=[]
        for row in self.rt.db.query('select external_id,data from automation_rules'):
            rule=json.loads(row['data'])
            if not rule.get('enabled') or rule.get('trigger')!=trigger or not self._matches(rule.get('conditions',{}),payload): continue
            key=self._run_key(event_id,row['external_id'])
            if self.rt.db.scalar('select count(*) from automation_runs where external_id=?',(key,)): out.append({'status':'duplicate','rule_id':row['external_id']}); continue
            if dry_run: out.append({'status':'would_execute','rule_id':row['external_id']}); continue
            action=rule['action']; policy=PolicyEngine(AutonomyMode(rule['mode']),self.kill_switch,spend_limit=0)
            decision=policy.authorize(action.get('type','action'),monetary=action.get('type')=='promotion_order',amount=float(action.get('amount',0) or 0),destructive=bool(action.get('destructive')),high_risk=bool(action.get('high_risk')))
            if not decision.allowed: out.append({'status':'approval' if decision.requires_approval else 'blocked','reason':decision.reason,'rule_id':row['external_id']}); continue
            if action.get('type')=='create_task': self.rt.db.execute('insert into lead_tasks(external_id,account_id,data) values(?,?,?)',(str(uuid.uuid4()),str(self.rt.account_id),json.dumps({'lead_id':payload.get('lead_id'),'title':action.get('title','Task')},ensure_ascii=False)))
            self.rt.db.execute('insert into automation_runs(external_id,account_id,data) values(?,?,?)',(key,str(self.rt.account_id),json.dumps({'event':event_id,'rule':row['external_id'],'status':'executed'})))
            out.append({'status':'executed','rule_id':row['external_id']})
        return out
