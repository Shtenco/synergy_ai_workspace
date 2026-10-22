import unittest,tempfile
from pathlib import Path
from workspace import service
from workspace.provider_runtime import dry_run_dispatch,inventory,source_manifest
class ProvidersV07(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=service.DB;service.DB=Path(self.tmp.name)/'db.sqlite'
  self.lead=service.create_lead('Sandbox contact','avito');self.action=service.prepare_action(self.lead,'avito.message','Approved draft')['id']
 def tearDown(self):service.DB=self.old;self.tmp.cleanup()
 def test_approval_gate(self):self.assertEqual(dry_run_dispatch(self.action,'avito','owner','one')['reason'],'APPROVAL_REQUIRED')
 def test_mock_dispatch_and_idempotency(self):
  service.approve_action(self.action);a=dry_run_dispatch(self.action,'avito','owner','id42');b=dry_run_dispatch(self.action,'avito','owner','id42')
  self.assertEqual(a['receipt']['delivery'],'NOT_SENT');self.assertTrue(b['replayed']);self.assertEqual(len([x for x in service.list_data('audit') if x['action']=='provider.dry_run']),1)
 def test_capability_mismatch(self):
  service.approve_action(self.action);self.assertEqual(dry_run_dispatch(self.action,'instagram','owner','other')['reason'],'CAPABILITY_MISMATCH')
 def test_live_disabled(self):
  self.assertTrue(all(not x['live_writes'] for x in inventory()['providers'].values()));self.assertEqual(service.execute_action(self.action)['code'],'NO_VERIFIED_PROVIDER_ADAPTER')
 def test_invalid_provider(self):
  with self.assertRaises(ValueError):dry_run_dispatch(self.action,'unknown','owner','id')
 def test_operator_required(self):
  with self.assertRaises(ValueError):dry_run_dispatch(self.action,'avito','','id')
 def test_manifest(self):self.assertTrue(source_manifest()['modules']['avito_original']['present'])
if __name__=='__main__':unittest.main()
