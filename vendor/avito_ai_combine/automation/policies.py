from enum import Enum
from dataclasses import dataclass
class AutonomyMode(str,Enum): OFF='OFF'; ADVISER='ADVISER'; COPILOT='COPILOT'; AUTOPILOT='AUTOPILOT'
class KillSwitch:
    def __init__(self): self.active=False
    def activate(self): self.active=True
    def deactivate(self): self.active=False
@dataclass(frozen=True)
class PolicyDecision: allowed:bool; requires_approval:bool=False; reason:str=''
class PolicyEngine:
    def __init__(self,mode=AutonomyMode.COPILOT,kill_switch=None,spend_limit=0): self.mode=mode; self.kill_switch=kill_switch or KillSwitch(); self.spend_limit=spend_limit
    def authorize(self,action,monetary=False,amount=0,destructive=False,high_risk=False):
        if self.kill_switch.active: return PolicyDecision(False,False,'kill_switch')
        if self.mode==AutonomyMode.OFF: return PolicyDecision(False,False,'off')
        if self.mode==AutonomyMode.ADVISER: return PolicyDecision(False,False,'adviser')
        if self.mode==AutonomyMode.COPILOT: return PolicyDecision(False,True,'approval_required')
        if monetary and amount>self.spend_limit: return PolicyDecision(False,True,'spend_limit')
        if destructive or high_risk: return PolicyDecision(False,True,'approval_required')
        return PolicyDecision(True,False,'allowed')
