from avito_ai_combine.ai.guardrails import guard
class SalesAgent:
    def __init__(self,gateway,knowledge): self.gateway=gateway; self.knowledge=knowledge
    def draft_reply(self,profile,request,controlled_facts=()):
        entries=self.knowledge.search_approved(profile); available={k:bool(entries) for k in controlled_facts}; g=guard(controlled_facts,available,not bool(entries))
        if not g['allowed']: return {'text':'','handoff':True,'reason':g['reason']}
        r=self.gateway.generate({'profile':profile,'request':request,'knowledge':[e.text for e in entries]}); return {'text':r.text,'handoff':r.uncertain,'reason':'uncertain' if r.uncertain else 'ok'}
