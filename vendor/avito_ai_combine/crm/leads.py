from dataclasses import dataclass,field
@dataclass
class Lead:
    id:str; avito_identity:str; source_listing:str|None=None; status:str='NEW'; score:int=0; intent:str='general'; reason_codes:list[str]=field(default_factory=list)
class LeadService:
    def __init__(self): self.by_identity={}
    def upsert_from_chat(self,identity,listing_id=None):
        if identity not in self.by_identity: self.by_identity[identity]=Lead(str(len(self.by_identity)+1),identity,listing_id)
        elif listing_id and not self.by_identity[identity].source_listing: self.by_identity[identity].source_listing=listing_id
        return self.by_identity[identity]
