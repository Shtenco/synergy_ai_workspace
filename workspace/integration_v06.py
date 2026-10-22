"""V0.6 deterministic integration: existing original adapters + reviewable work items.
No live provider tokens or external writes are accepted.
"""
from __future__ import annotations
import json
from workspace import service, adapters

VALID={'smm.post','smm.message','avito.message','avito.listing_update'}

def prepare_lead_workflow(lead_id:int, kind:str, request:dict)->dict:
    if kind not in VALID: raise ValueError('unsupported capability')
    if not isinstance(request,dict): raise ValueError('request object required')
    with service.LOCK,service.connect() as db:
        lead=db.execute('SELECT id,name,source,notes FROM leads WHERE id=?',(lead_id,)).fetchone()
        if lead is None:raise LookupError('lead')
        lead=dict(lead)
    evidence={'lead_id':lead_id,'source':lead['source'],'capability':kind,'provider_dispatch':'DISABLED'}
    if kind.startswith('avito.'):
        metrics=request.get('metrics',{})
        score=adapters.avito_score(metrics)
        evidence['original_adapter']=score['source'];evidence['lead_score']=score['value'];evidence['reason_codes']=score['reason_codes']
        draft=request.get('draft') or f'Здравствуйте! По вашему обращению: {lead["name"]}. Подготовим индивидуальный ответ после проверки оператором.'
    else:
        plan=adapters.autopilot_plan({'product':request.get('product','SYNERGY'), 'audience':request.get('audience','клиенты'), 'days':1,'platforms':[request.get('platform','telegram')]})
        if not plan.get('items'):raise ValueError('empty agent plan')
        evidence['original_adapter']='agi_autopilot.agents.smm.SMMAgent.content_plan'
        evidence['plan_item']=plan['items'][0]
        draft=request.get('draft') or plan['items'][0]['brief']
    output=service.prepare_action(lead_id,kind,draft)
    with service.LOCK,service.connect() as db:
        service.emit(db,'workflow.agent_draft',str(output['id']),evidence)
    return {'action':output,'draft':draft,'evidence':evidence,'provider_execution':False}

def simulate_provider(action_id:int)->dict:
    """Read-only local test transport: no HTTP, no credentials, no actual messages."""
    with service.LOCK,service.connect() as db:
        row=db.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone()
        if row is None:raise LookupError('action')
        row=dict(row)
        if row['status']!='approved':
            service.emit(db,'sandbox.deny',str(action_id),{'reason':'APPROVAL_REQUIRED'})
            return {'status':'denied','reason':'APPROVAL_REQUIRED','external_effects':False}
        receipt={'transport':'SYNERGY_LOCAL_SIMULATOR','action_id':action_id,'kind':row['kind'],'payload_length':len(row['draft']),'delivery':'NOT_SENT'}
        service.emit(db,'sandbox.simulated',str(action_id),receipt)
        return {'status':'simulated','receipt':receipt,'external_effects':False}
