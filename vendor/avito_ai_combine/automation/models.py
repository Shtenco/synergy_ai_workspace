from dataclasses import dataclass
@dataclass
class AutomationRule: trigger:str; conditions:dict; actions:list; enabled:bool=True
