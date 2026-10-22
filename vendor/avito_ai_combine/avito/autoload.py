class AutoloadClient:
    def __init__(self,t,token): self.t=t; self.token=token
    def uploads(self): return self.t.request('GET','/autoload/v4/uploads',token=self.token)
    def current(self): return self.t.request('GET','/autoload/v4/uploads/current',token=self.token)
    def category_tree(self): return self.t.request('GET','/autoload/v1/user-docs/tree',token=self.token)
