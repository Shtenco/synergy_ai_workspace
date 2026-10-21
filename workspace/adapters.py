"""Read-only adapters to ORIGINAL SYNERGY sources; no network or external actions."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import sys

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'vendor'
CABINETS=['index.html','cabinet.html','workspaces.html','studio.html','lead-radar.html','ai-studio.html','caseflow.html','parsing.html','engagement.html','jobs.html']

def inventory():
    smm=V/'synergy.github.io'/'smm'
    py=V/'python-runtime'/'src'/'agi_autopilot'
    desktop=V/'desktop-integration'/'apps'/'desktop'
    avito=V/'avito_ai_combine'
    return {
        'smm':{'source_path':str(smm),'available':smm.is_dir(),'cabinet_files':[{'name':n,'available':(smm/n).is_file()} for n in CABINETS]},
        'autopilot':{'source_path':str(py),'available':(py/'agents'/'smm.py').is_file(),'desktop_original_available':(desktop/'src'/'App.tsx').is_file(),'agents':[{'name':n,'available':(py/'agents'/f'{n}.py').is_file()} for n in ['ceo','cfo','smm','sales','video','revenue','coder','verifier']]},
        'avito':{'source_path':str(avito),'available':(avito/'crm'/'scoring.py').is_file(),'capabilities':['crm.lead_score']},
        'external_execution_enabled':False}

def avito_score(payload):
    """Calls the actual vendored AVITO LeadScorer, never a rewritten score model."""
    if not isinstance(payload,dict):raise ValueError('payload must be an object')
    from vendor.avito_ai_combine.crm.scoring import LeadScorer
    allowed={'intent_strength','contact_language','conversation_progression','call_signal','repeated_engagement','spam','manual_adjustment'}
    data={k:v for k,v in payload.items() if k in allowed}
    try: score=LeadScorer().score(data)
    except (ValueError,TypeError,OverflowError) as e:raise ValueError('invalid lead scoring parameters') from e
    return {'source':'vendor.avito_ai_combine.crm.scoring.LeadScorer','value':score.value,'reason_codes':list(score.reason_codes),'external_effects':False,'verified_buyer':False}

def autopilot_plan(payload):
    """Read-only access to the exact original SMMAgent from the separately imported Python branch."""
    if not isinstance(payload,dict):raise ValueError('payload must be an object')
    src=V/'python-runtime'/'src'/'agi_autopilot'/'agents'/'smm.py'
    if not src.is_file():raise FileNotFoundError('Import feat/capability-runtime-v1 first')
    spec=importlib.util.spec_from_file_location('synergy_imported_smm_agent',src)
    if spec is None or spec.loader is None:raise RuntimeError('cannot load original SMMAgent')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    try: return module.SMMAgent().content_plan(payload)
    except (ValueError,TypeError,OverflowError) as e:raise ValueError('invalid content plan parameters') from e
