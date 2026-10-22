class AutomationEngine:
    def __init__(self,policy): self.policy=policy; self.executed=set()
    def execute(self,event_id,rule_id,action_id,fn,**policy_kwargs):
        key=(event_id,rule_id,action_id)
        if key in self.executed: return {'status':'duplicate'}
        d=self.policy.authorize(action_id,**policy_kwargs)
        if not d.allowed: return {'status':'approval' if d.requires_approval else 'blocked','reason':d.reason}
        result=fn(); self.executed.add(key); return {'status':'executed','result':result}
