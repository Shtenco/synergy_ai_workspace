class ListingsClient:
    def __init__(self,t,token): self.t=t; self.token=token
    def list(self,**params): return self.t.request('GET','/core/v1/items',token=self.token,params=params or None)
    def update_price(self,user_id,item_id,price,key): return self.t.request('POST',f'/core/v1/accounts/{user_id}/items/{item_id}/update_price',token=self.token,json_body={'price':price},idempotency_key=key)
