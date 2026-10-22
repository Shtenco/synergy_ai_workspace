import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from workspace import service
from workspace.integration_v06 import prepare_lead_workflow,simulate_provider

class IntegrationV06(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.old=service.DB;service.DB=Path(self.t.name)/'db.sqlite'
 def tearDown(self):service.DB=self.old;self.t.cleanup()
 def test_avito_full_dry_run(self):
  lid=service.create_lead('Test Customer','avito')
  r=prepare_lead_workflow(lid,'avito.message',{'metrics':{'intent_strength':1}})
  aid=r['action']['id'];self.assertTrue(r['evidence']['original_adapter'].endswith('LeadScorer'))
  self.assertEqual(simulate_provider(aid)['reason'],'APPROVAL_REQUIRED')
  service.approve_action(aid)
  receipt=simulate_provider(aid)
  self.assertEqual(receipt['receipt']['delivery'],'NOT_SENT')
  self.assertFalse(receipt['external_effects'])
  self.assertEqual(service.execute_action(aid)['code'],'NO_VERIFIED_PROVIDER_ADAPTER')
  events=[x['action'] for x in service.list_data('audit')]
  self.assertIn('sandbox.simulated',events);self.assertIn('workflow.agent_draft',events)
 def test_missing_smm_source_fails_closed(self):
  lid=service.create_lead('Test Customer','smm')
  with patch('workspace.adapters.autopilot_plan',side_effect=FileNotFoundError('source')):
   with self.assertRaises(FileNotFoundError):prepare_lead_workflow(lid,'smm.post',{})
  self.assertFalse(service.list_data('actions'))
 def test_original_agent_planning_mocked_contract(self):
  lid=service.create_lead('A','smm')
  with patch('workspace.adapters.autopilot_plan',return_value={'items':[{'brief':'draft from agent','platform':'vk'}]}):
   r=prepare_lead_workflow(lid,'smm.post',{'product':'P','platform':'vk'})
  self.assertEqual(r['draft'],'draft from agent');self.assertEqual(r['evidence']['plan_item']['platform'],'vk')
 def test_invalid_kind_is_denied(self):
  lid=service.create_lead('A','avito')
  with self.assertRaises(ValueError):prepare_lead_workflow(lid,'host.shell',{})
 def test_404_missing_action(self):
  with self.assertRaises(LookupError):simulate_provider(666)

if __name__=='__main__':unittest.main()
