import tempfile,unittest
from pathlib import Path
from workspace import service as s
class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();s.DB=Path(self.tmp.name)/'integration.sqlite3'
 def tearDown(self):self.tmp.cleanup()
 def test_lead_draft_approve_block_and_audit(self):
  lead=s.create_lead('Buyer','avito')
  a=s.prepare_action(lead,'avito.message','Согласованный шаблон')
  self.assertEqual(s.list_data('tasks')[0]['status'],'review')
  self.assertEqual(s.approve_action(a['id'])['status'],'approved')
  with self.assertRaises(ValueError):s.approve_action(a['id'])
  result=s.execute_action(a['id'])
  self.assertEqual(result['code'],'NO_VERIFIED_PROVIDER_ADAPTER')
  self.assertEqual(s.list_data('actions')[0]['status'],'approved')
  self.assertTrue(any(e['action']=='action.execute_denied' for e in s.list_data('audit')))
 def test_reject_bad_inputs(self):
  with self.assertRaises(LookupError):s.prepare_action(99,'avito.message','text')
  lid=s.create_lead('Test','manual')
  with self.assertRaises(ValueError):s.prepare_action(lid,'host.shell','rm -rf /')
  with self.assertRaises(LookupError):s.execute_action(999)
