class ReviewsClient:
    def __init__(self,t,token): self.t=t; self.token=token
    def list(self,**params): return self.t.request('GET','/ratings/v1/reviews',token=self.token,params=params or None)
