from dataclasses import dataclass
@dataclass(frozen=True)
class CapabilitySet:
    scopes:frozenset[str]
    flags:frozenset[str]=frozenset()
    def allows(self,name): return name in self.scopes or name in self.flags
class CapabilityResolver:
    def __init__(self,scopes=(),flags=()): self.value=CapabilitySet(frozenset(scopes),frozenset(flags))
    def resolve(self,account_id): return self.value
