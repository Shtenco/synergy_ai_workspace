from __future__ import annotations

class SMMAgent:
    def content_plan(self,p:dict)->dict:
        product=str(p.get("product","продукт")); audience=str(p.get("audience","целевая аудитория")); objective=str(p.get("objective","лиды")); days=max(1,min(31,int(p.get("days",14))))
        platforms=p.get("platforms") or ["telegram","vk","instagram"]
        pillars=["problem","proof","education","case","offer","behind_the_scenes","faq"]
        items=[]
        for i in range(days):
            pillar=pillars[i%len(pillars)]; platform=platforms[i%len(platforms)]
            items.append({"day":i+1,"platform":platform,"pillar":pillar,"brief":f"{pillar}: {product} для {audience}; цель — {objective}","cta":"one measurable next step"})
        return {"schema":"synergy.smm-plan/v1","items":items,"external_effects":False}

    def analyze_metrics(self,p:dict)->dict:
        impr=float(p.get("impressions",0) or 0); reach=float(p.get("reach",0) or 0); clicks=float(p.get("clicks",0) or 0); leads=float(p.get("leads",0) or 0); spend=float(p.get("spend_usd",0) or 0); revenue=float(p.get("revenue_usd",0) or 0)
        return {"schema":"synergy.smm-metrics/v1","ctr_pct":(clicks/impr*100 if impr else None),"lead_rate_pct":(leads/clicks*100 if clicks else None),"cpl_usd":(spend/leads if leads else None),"roas":(revenue/spend if spend else None),"reach":reach}

    def post_brief(self,p:dict)->dict:
        return {"schema":"synergy.smm-copy-brief/v1","platform":p.get("platform","telegram"),"hook":p.get("hook") or f"Почему {p.get('product','продукт')} важен прямо сейчас", "body_points":p.get("points") or ["проблема","решение","доказательство"], "cta":p.get("cta") or "Напишите, если нужен пример", "external_effects":False}
