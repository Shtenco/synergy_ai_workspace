import unittest
from workspace import adapters
class AdaptersTests(unittest.TestCase):
 def test_original_avito_score(self):
  x=adapters.avito_score({'intent_strength':1,'contact_language':True})
  self.assertEqual(x['value'],55)
  self.assertIn('LeadScorer',x['source'])
  self.assertFalse(x['verified_buyer'])
 def test_inventory(self):
  x=adapters.inventory()
  self.assertTrue(x['avito']['available'])
  self.assertFalse(x['external_execution_enabled'])
 def test_import_guard(self):
  if not adapters.inventory()['autopilot']['available']:
   with self.assertRaises(FileNotFoundError):adapters.autopilot_plan({'product':'test'})
if __name__=='__main__':unittest.main()
