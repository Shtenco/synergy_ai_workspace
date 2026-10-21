from __future__ import annotations
import json, os
from .agents import CEOAgent,CFOAgent,SMMAgent,SalesAgent,VideoAgent,RevenueAgent,CoderAgent,VerifierAgent
from .capabilities import CapabilityRegistry,CapabilitySpec,Effect
from .integrations import BusinessIntegrations, GenericVideoProvider
from .model_router import TextModelRouter
from .policy import PolicyEngine
from .task_store import TaskStore


class AutopilotRuntime:
    def __init__(self,db_path:str|None=None):
        self.store=TaskStore(db_path or os.getenv("AUTOPILOT_DB_PATH","var/autopilot_runtime.db")); self.policy=PolicyEngine(); self.registry=CapabilityRegistry()
        self.ceo=CEOAgent(); self.revenue=RevenueAgent(); self.coder=CoderAgent(); self.verifier=VerifierAgent(); self.cfo=CFOAgent(); self.smm=SMMAgent(); self.sales=SalesAgent(); self.video=VideoAgent(); self.biz=BusinessIntegrations(); self.video_provider=GenericVideoProvider(); self.models=TextModelRouter()
        self._register()
    def _r(self,name,agent,effect,desc,handler,approval=False,lineage="AUTOPILOT2/V5"):
        self.registry.register(CapabilitySpec(name,agent,effect,desc,approval,True,lineage),handler)
    def _register(self):
        self._r("coder.change_plan","AI_CODER",Effect.LOCAL_COMPUTE,"Prepare a bounded code-change plan without shell execution",self.coder.change_plan,False,"AUTOPILOT2/V5 Coder")
        self._r("verifier.check_evidence","AI_VERIFIER",Effect.LOCAL_COMPUTE,"Verify required evidence fields without granting domain authority",self.verifier.check_evidence,False,"AUTOPILOT2/V5 Verifier")
        self._r("research.validate_revenue_opportunity","AI_REVENUE",Effect.LOCAL_COMPUTE,"Evidence-first validation of a revenue opportunity",self.revenue.validate,False,"Auto-Company 2.0 revenue-loop + AUTOPILOT")
        self._r("ceo.plan","AI_CEO",Effect.LOCAL_COMPUTE,"Decompose a business goal into bounded capabilities",self.ceo.plan,False,"AUTOPILOT2/V5 planner + Federation V3")
        self._r("cfo.analyze_budget","AI_CFO",Effect.LOCAL_COMPUTE,"Budget, margin, variance and ROAS analysis",self.cfo.analyze_budget)
        self._r("cfo.unit_economics","AI_CFO",Effect.LOCAL_COMPUTE,"CAC/LTV/payback/contribution analysis",self.cfo.unit_economics)
        self._r("cfo.capital_proposal","AI_CFO",Effect.LOCAL_COMPUTE,"Non-authoritative capital capacity proposal",self.cfo.capital_proposal)
        self._r("smm.content_plan","AI_SMM",Effect.LOCAL_COMPUTE,"Cross-platform content plan",self.smm.content_plan,False,"AUTOPILOT2/V5 + SMM AI BOT")
        self._r("smm.analyze_metrics","AI_SMM",Effect.LOCAL_COMPUTE,"CTR/CPL/lead-rate/ROAS analysis",self.smm.analyze_metrics,False,"SMM AI BOT")
        self._r("smm.post_brief","AI_SMM",Effect.LOCAL_COMPUTE,"Create a platform post brief",self.smm.post_brief,False,"AUTOPILOT2/V5 + SMM AI BOT")
        self._r("sales.qualify","AI_SALES",Effect.LOCAL_COMPUTE,"Lead score/stage/objection classification",self.sales.qualify,False,"AI-Sales-Bot")
        self._r("sales.compose_cold_open","AI_SALES",Effect.LOCAL_COMPUTE,"Create one cold-open draft, not send it",lambda p:self.sales.compose(p,"cold_open"),False,"AI-Sales-Bot")
        self._r("sales.compose_followup","AI_SALES",Effect.LOCAL_COMPUTE,"Create respectful follow-up draft",lambda p:self.sales.compose(p,"follow_up"),False,"AI-Sales-Bot")
        self._r("sales.compose_objection","AI_SALES",Effect.LOCAL_COMPUTE,"Draft objection response",lambda p:self.sales.compose(p,"objection"),False,"AI-Sales-Bot")
        self._r("sales.compose_offer","AI_SALES",Effect.LOCAL_COMPUTE,"Draft next-step/offer copy",lambda p:self.sales.compose(p,"offer"),False,"AI-Sales-Bot")
        self._r("video.storyboard","AI_VIDEO",Effect.LOCAL_COMPUTE,"Video/Reels/Shorts storyboard and asset plan",self.video.storyboard,False,"NEW from legacy video/reels publish evidence")
        self._r("video.render_request","AI_VIDEO",Effect.LOCAL_COMPUTE,"Prepare provider-neutral render request without spending money",self.video.render_request,False,"NEW provider-agnostic render boundary")
        self._r("video.render","AI_VIDEO",Effect.PAID_API,"Dispatch a configured reviewed video-render sidecar/provider",self.video_provider.render,True,"NEW provider-agnostic paid render boundary")
        self._r("integration.status","BUSINESS_API",Effect.READ,"Configured business integration status",lambda p:self.biz.status(),False,"AUTOPILOT2/V5")
        self._r("telegram.send_message","AI_SMM",Effect.EXTERNAL_WRITE,"Telegram Bot API sendMessage",self.biz.telegram_send,True,"AUTOPILOT2/V5")
        self._r("telegram.send_video","AI_VIDEO",Effect.EXTERNAL_WRITE,"Telegram Bot API sendVideo",self.biz.telegram_video,True,"AUTOPILOT2/V5")
        self._r("vk.wall_post","AI_SMM",Effect.EXTERNAL_WRITE,"VK official API wall post",self.biz.vk_wall_post,True,"AUTOPILOT2/V5 + SMM AI BOT")
        self._r("vk.stats","AI_SMM",Effect.READ,"VK group statistics",self.biz.vk_stats,False,"AUTOPILOT2/V5")
        self._r("facebook.page_post","AI_SMM",Effect.EXTERNAL_WRITE,"Facebook Page official Graph API post",self.biz.facebook_page_post,True,"SMM AI BOT + AUTOPILOT2/V5")
        self._r("instagram.publish","AI_SMM",Effect.EXTERNAL_WRITE,"Instagram Business image/video/reels/story publish",self.biz.instagram_publish,True,"SMM AI BOT")
        self._r("whatsapp.send_text","AI_SALES",Effect.EXTERNAL_WRITE,"WhatsApp Business text send in permitted conversation",self.biz.whatsapp_text,True,"AUTOPILOT2/V5 + SMM AI BOT")
        self._r("discord.send","AI_SMM",Effect.EXTERNAL_WRITE,"Discord webhook send",self.biz.discord_send,True,"AUTOPILOT2/V5")
        self._r("crm.bitrix24.leads","AI_SALES",Effect.READ,"Read Bitrix24 leads",self.biz.bitrix_leads,False,"AUTOPILOT2/V5")
        self._r("crm.bitrix24.lead_add","AI_SALES",Effect.CRM_WRITE,"Create Bitrix24 lead",self.biz.bitrix_lead_add,True,"AUTOPILOT2/V5")
        self._r("crm.amocrm.leads","AI_SALES",Effect.READ,"Read amoCRM leads",self.biz.amocrm_leads,False,"AUTOPILOT2/V5")
        self._r("crm.retail.orders","AI_SALES",Effect.READ,"Read RetailCRM orders",self.biz.retail_orders,False,"AUTOPILOT2/V5")
        self._r("crm.onec.orders","AI_CFO",Effect.READ,"Read a configured 1C HTTP service resource",self.biz.onec_orders,False,"AUTOPILOT2/V5")
        self._r("ads.yandex.campaigns","AI_ADS",Effect.READ,"Read Yandex Direct campaigns",self.biz.yandex_direct_campaigns,False,"AUTOPILOT2/V5")
        self._r("ads.facebook.campaigns","AI_ADS",Effect.READ,"Read Meta/Facebook Ads campaigns",self.biz.facebook_ads_campaigns,False,"AUTOPILOT2/V5")
        self._r("youtube.search","AI_VIDEO",Effect.READ,"YouTube Data API search",self.biz.youtube_search,False,"AUTOPILOT2/V5")
        self._r("email.send","AI_SALES",Effect.EXTERNAL_WRITE,"SMTP email send",self.biz.email_send,True,"AUTOPILOT2/V5")
        for name,effect in [("payment.execute",Effect.PAYMENT),("accounting.book",Effect.ACCOUNTING),("blockchain.submit",Effect.BLOCKCHAIN),("host.shell",Effect.HOST_EXEC)]:
            self._r(name,"DENIED_DOMAIN",effect,"Reserved authority outside AUTOPILOT",lambda p:{"never":True},True,"SYNERGY authority boundary")

    def submit(self,capability:str,params:dict,idempotency_key:str|None=None)->dict:
        spec=self.registry.spec(capability); t=self.store.create(capability,params,idempotency_key); dec=self.policy.decide(t["id"],spec,False)
        status={"ALLOW":"ready","REQUIRE_APPROVAL":"needs_approval","DENY":"denied","DEFER":"deferred"}[dec.decision]
        return self.store.update(t["id"],status=status,policy_json=json.dumps(dec.as_payload(),ensure_ascii=False))
    def submit_goal(self,goal:str,context:dict|None=None,metadata:dict|None=None)->dict:
        return self.submit("ceo.plan",{"goal":goal,"context":context or {},"metadata":metadata or {}},(metadata or {}).get("idempotency_key"))
    def approve(self,tid:str,actor:str)->dict:
        t=self.store.get(tid)
        if t["status"]!="needs_approval": raise ValueError("task is not awaiting approval")
        return self.store.update(tid,status="approved",approved_by=actor)
    def execute(self,tid:str)->dict:
        t=self.store.get(tid); spec=self.registry.spec(t["capability"]); approved=bool(t.get("approved_by")); dec=self.policy.decide(tid,spec,approved)
        self.store.update(tid,policy_json=json.dumps(dec.as_payload(),ensure_ascii=False))
        if dec.decision!="ALLOW":
            status="needs_approval" if dec.decision=="REQUIRE_APPROVAL" else "denied"; return self.store.update(tid,status=status)
        if spec.effect not in {Effect.READ,Effect.LOCAL_COMPUTE} and not self.policy.external_effects_enabled():
            return self.store.update(tid,status="denied",error="AUTOPILOT_EXTERNAL_EFFECTS is disabled")
        self.store.update(tid,status="running")
        try:
            result=self.registry.handler(t["capability"])(t["params"])
            return self.store.update(tid,status="succeeded",result_json=json.dumps(result,ensure_ascii=False,default=str),error=None)
        except Exception as e:
            return self.store.update(tid,status="failed",error=f"{type(e).__name__}: {e}")
