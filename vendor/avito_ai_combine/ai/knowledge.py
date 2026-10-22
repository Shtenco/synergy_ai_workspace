from dataclasses import dataclass
from datetime import date
@dataclass
class KnowledgeEntry:
    text:str; profile:str='general'; approved:bool=False; valid_from:date|None=None; valid_to:date|None=None
    def usable(self,on=None):
        on=on or date.today(); return self.approved and (self.valid_from is None or self.valid_from<=on) and (self.valid_to is None or on<=self.valid_to)
class KnowledgeService:
    def __init__(self,entries=()): self.entries=list(entries)
    def add(self,entry): self.entries.append(entry); return entry
    def search_approved(self,profile): return [e for e in self.entries if e.usable() and e.profile in (profile,'general')]
