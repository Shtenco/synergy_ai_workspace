from dataclasses import dataclass
@dataclass(frozen=True)
class LeadScore: value:int; reason_codes:tuple[str,...]
class LeadScorer:
    def score(self,s):
        v=0; r=[]
        if s.get('intent_strength',0): v+=30*min(1,float(s['intent_strength'])); r.append('intent_strength')
        if s.get('contact_language'): v+=25; r.append('contact_language')
        if s.get('conversation_progression'): v+=15; r.append('conversation_progression')
        if s.get('call_signal'): v+=15; r.append('call_signal')
        if s.get('repeated_engagement'): v+=10; r.append('repeated_engagement')
        if s.get('spam'): v-=50; r.append('spam')
        v+=float(s.get('manual_adjustment',0));
        return LeadScore(max(0,min(100,round(v))),tuple(r))
