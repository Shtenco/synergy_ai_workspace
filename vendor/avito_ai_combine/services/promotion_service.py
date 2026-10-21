class PromotionService:
    def __init__(self,client,policy): self.client=client; self.policy=policy; self.orders={}
    def recommend(self,metrics):
        if metrics.get('contact_rate') is not None and metrics['contact_rate']<.015: return 'REVIEW_LISTING'
        return 'NO_ACTION'
    def execute(self,payload,key,amount):
        if key in self.orders: return self.orders[key]
        d=self.policy.authorize('promotion_order',monetary=True,amount=amount)
        if not d.allowed: return {'status':'approval' if d.requires_approval else 'blocked','reason':d.reason}
        r=self.client.create_order(payload,key); self.orders[key]=r; return r
