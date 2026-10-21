class AutoloadService:
    def __init__(self,client): self.client=client
    def validate(self,items): return [f'item {i}: title required' for i,x in enumerate(items) if not x.get('title')]
    def can_upload(self,items): return not self.validate(items)
