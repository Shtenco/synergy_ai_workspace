"""SYNERGY policy-limited internal orchestration, independent of external providers.

Adapter contract deliberately compatible with a future authenticated META-API gateway:
capability_id, schema, source, needs_approval, state.
"""
from __future__ import annotations
from hashlib import sha256
import json
from . import capital_engine, service

CAPABILITIES=(
 {"id":"workspace.tasks.list","category":"workspace","effect":"read","requires_approval":False,"source":"synergy_ai_workspace.workspace.service"},
 {"id":"workspace.capital.summary","category":"finance","effect":"read","requires_approval":False,"source":"synergy_ai_workspace.workspace.capital_engine"},
 {"id":"workspace.capital.allocate.plan","category":"finance","effect":"local_write_draft","requires_approval":False,"source":"synergy_ai_workspace.workspace.capital_engine"},
 {"id":"external.avito.publish","category":"external","effect":"blocked","requires_approval":True,"source":"not-connected"},
 {"id":"external.investment.trade","category":"external","effect":"blocked","requires_approval":True,"source":"not-connected"}
)
_ALLOWED={x["id"] for x in CAPABILITIES if x["effect"]!="blocked"}
def list_capabilities():
 return {"capabilities":[dict(x) for x in CAPABILITIES],"external_execution":False,"meta_api_live_connected":False}

def run(steps):
 if not isinstance(steps,list) or not 1<=len(steps)<=10:raise ValueError("1..10 steps expected")
 normalized=[]
 for step in steps:
  if not isinstance(step,dict) or not isinstance(step.get("capability"),str) or not isinstance(step.get("arguments",{}),dict):
   raise ValueError("invalid workflow step")
  if step["capability"] not in _ALLOWED:raise PermissionError("CAPABILITY_DENIED")
  normalized.append((step["capability"],step.get("arguments",{})))
 results=[]
 for capability,args in normalized:
  if capability=="workspace.tasks.list":
   if args:raise ValueError("tasks.list takes no arguments")
   output={"items":service.list_data("tasks",limit=100)}
  elif capability=="workspace.capital.summary":
   if set(args)!={"currency","start","end"}:raise ValueError("summary requires currency/start/end only")
   output=capital_engine.summary(args["currency"],args["start"],args["end"])
  elif capability=="workspace.capital.allocate.plan":
   allowed={"currency","start","end","reserve_pct","investment_pct","minimum_buffer"}
   if set(args)-allowed:raise ValueError("unknown allocation arguments")
   if not {"currency","start","end","reserve_pct","investment_pct"}<=set(args):raise ValueError("missing allocation fields")
   output=capital_engine.allocation_plan(args["currency"],args["start"],args["end"],args["reserve_pct"],args["investment_pct"],args.get("minimum_buffer","0"))
  else:raise PermissionError("CAPABILITY_DENIED")
  results.append({"capability":capability,"result":output})
 receipt=sha256(json.dumps(results,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 with service.LOCK,service.connect() as db:
  service.emit(db,"orchestration.complete","local",{"sha256":receipt,"steps":len(results),"external_effects":False})
 return {"status":"completed_local","results":results,"receipt_sha256":receipt,"external_effects":False,"provider_actions":False}
