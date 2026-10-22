from dataclasses import dataclass
@dataclass
class AIResult: text:str; uncertain:bool=False
class AIGateway:
    def __init__(self,provider=None): self.provider=provider
    def generate(self,request):
        if self.provider is None: return AIResult('',True)
        return self.provider.generate(request)
