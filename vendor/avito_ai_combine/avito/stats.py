class StatsClient:
    def __init__(self,t,token,user_id): self.t=t; self.token=token; self.user_id=user_id
    def items(self,item_ids,date_from,date_to): return self.t.request('POST',f'/stats/v2/accounts/{self.user_id}/items',token=self.token,json_body={'itemIds':item_ids,'dateFrom':date_from,'dateTo':date_to})
