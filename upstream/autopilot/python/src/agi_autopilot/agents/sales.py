from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum


class Stage(StrEnum):
    COLD_OPEN="cold_open"; DISCOVERY="discovery"; QUALIFIED="qualified"; OBJECTION="objection"; OFFER="offer"; CLOSE="close"; FOLLOWUP="followup"; LOST="lost"

OBJECTIONS={"price":["дорого","цена","expensive"],"timing":["позже","не сейчас","later"],"trust":["не довер","гарант","trust"],"refusal":["не интересно","откаж","не нужно","stop"]}


def detect_objection(text:str)->str|None:
    low=text.lower()
    for key, words in OBJECTIONS.items():
        if any(w in low for w in words): return key
    return None


def interest_score(text:str)->int:
    low=text.lower(); score=0
    for w,n in [("цена",8),("сколько",8),("куп",15),("заказ",15),("демо",12),("созвон",12),("интерес",10),("да",5),("no",-8),("нет",-8)]:
        if w in low: score += n
    return max(-20,min(30,score))

@dataclass
class LeadState:
    lead_id:str; platform:str="crm"; name:str=""; stage:Stage=Stage.COLD_OPEN; score:int=0; history:list[dict]=field(default_factory=list); objections:list[str]=field(default_factory=list)

class SalesAgent:
    def qualify(self,p:dict)->dict:
        text=str(p.get("message", "")); base=int(p.get("current_score",0) or 0); obj=detect_objection(text); score=max(0,min(100,base+interest_score(text)+(10 if len(text)>80 else 0)))
        if obj=="refusal": stage=Stage.LOST
        elif obj: stage=Stage.OBJECTION
        elif score>=80: stage=Stage.CLOSE
        elif score>=50: stage=Stage.OFFER
        elif score>=20: stage=Stage.QUALIFIED
        else: stage=Stage.DISCOVERY
        return {"schema":"synergy.sales-qualification/v1","score":score,"stage":stage.value,"objection":obj,"recommended_next_action": "stop" if stage==Stage.LOST else ("prepare_close" if stage==Stage.CLOSE else "continue_dialogue")}

    def compose(self,p:dict,kind:str)->dict:
        product=str(p.get("product","продукт")); value=str(p.get("value","полезный результат")); name=str(p.get("name","")).strip(); prefix=(f"{name}, " if name else "")
        if kind=="cold_open": msg=f"{prefix}добрый день. Увидел возможную задачу, где {product} может дать {value}. Могу кратко показать, как это применить к вашей ситуации?"
        elif kind=="follow_up": msg=f"{prefix}возвращаюсь к сообщению выше. Чтобы не отвлекать: могу прислать один конкретный пример по {product}; если неактуально — больше писать не буду."
        elif kind=="objection": msg=f"Понимаю. По {product} предлагаю не спорить, а проверить один измеримый критерий: {value}. Если он не достигается, идею можно сразу закрыть."
        else: msg=f"Предлагаю следующий шаг по {product}: зафиксировать ожидаемый результат ({value}), срок и критерий приёмки."
        return {"schema":"synergy.sales-message/v1","kind":kind,"message":msg,"delivery_authority":"NONE","note":"Generated copy only; sending is a separate approved capability."}
