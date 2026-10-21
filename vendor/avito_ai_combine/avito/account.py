class AccountClient:
    def __init__(self,t,token): self.t=t; self.token=token
    def get_self(self): return self.t.request('GET','/core/v1/accounts/self',token=self.token)
