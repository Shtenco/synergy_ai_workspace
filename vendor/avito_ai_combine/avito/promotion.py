class PromotionClient:
    def __init__(self,t,token): self.t=t; self.token=token
    def services(self,item_ids): return self.t.request('POST','/promotion/v2/items/services/get',token=self.token,json_body={'itemIds':item_ids})
    def forecasts(self,payload): return self.t.request('POST','/promotion/v1/items/forecasts/get',token=self.token,json_body=payload)
    def create_order(self,payload,key): return self.t.request('POST','/promotion/v1/orders/create',token=self.token,json_body=payload,idempotency_key=key)
