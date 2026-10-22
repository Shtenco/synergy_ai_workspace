class CallsClient:
    def __init__(self,t,token,user_id): self.t=t; self.token=token; self.user_id=user_id
    def stats(self,payload): return self.t.request('POST',f'/core/v1/accounts/{self.user_id}/calls/stats/',token=self.token,json_body=payload)
