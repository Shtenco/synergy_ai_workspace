"""Financial imports are real local computations; banking attestation is NOT provided."""
import os, unittest, tempfile
from pathlib import Path
from workspace import service
from workspace import capital_engine as c

class TestCapitalEngine(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  service.DB=Path(self.tmp.name)/"finance.db"
  self.base={"source_id":"bank-example:2026-10","currency":"KZT","period_start":"2026-10-01","period_end":"2026-10-31",
   "entries":[
    {"entry_id":"1","date":"2026-10-01","kind":"income","amount":"300000.00","memo":"Revenue"},
    {"entry_id":"2","date":"2026-10-02","kind":"expense","amount":"120000.00","memo":"Operating costs"},
    {"entry_id":"3","date":"2026-10-03","kind":"transfer","amount":"500000.00"},
    {"entry_id":"4","date":"2026-10-04","kind":"investment","amount":"10000.00"}]}
 def tearDown(self):self.tmp.cleanup()
 def test_import_and_replay_idempotency(self):
  first=c.import_entries(self.base)
  self.assertEqual(first["imported"],4)
  replay=c.import_entries(self.base)
  self.assertEqual(replay["status"],"duplicate_ignored")
  d=c.summary("KZT","2026-10-01","2026-10-31")
  self.assertEqual(d["income_minor"],30000000)
  self.assertEqual(d["expense_minor"],12000000)
  self.assertEqual(d["delta_minor"],18000000)
  self.assertEqual(d["transfers_minor"],50000000)
  self.assertFalse(d["verified_by_bank"])
  self.assertEqual(d["source_count"],1)
  self.assertEqual(len(service.list_data("audit")),1)
 def test_different_source_payload_denied(self):
  c.import_entries(self.base)
  self.base["entries"][0]["amount"]="300001.00"
  with self.assertRaisesRegex(ValueError,"SOURCE_CONFLICT"):c.import_entries(self.base)
 def test_duplicate_ids_and_bad_currency_denied(self):
  self.base["entries"][1]["entry_id"]="1"
  with self.assertRaises(ValueError):c.import_entries(self.base)
  self.base["entries"][1]["entry_id"]="2"
  self.base["entries"][1]["currency"]="USD"
  with self.assertRaises(ValueError):c.import_entries(self.base)
 def test_amount_guard(self):
  for value in ["NaN","Infinity","-1","1.001",1.1,True,None]:
   with self.subTest(value=value):
    self.base["entries"][0]["amount"]=value
    with self.assertRaises(ValueError):c.import_entries(self.base)
 def test_positive_plan(self):
  c.import_entries(self.base)
  p=c.allocation_plan("KZT","2026-10-01","2026-10-31","20","50","5000")
  self.assertEqual(p["delta_minor"],18000000)
  self.assertEqual(p["liquidity_buffer_minor"],500000)
  self.assertEqual(p["reserve_minor"],3500000)
  self.assertEqual(p["investable_minor"],7000000)
  self.assertFalse(p["trading_enabled"])
  self.assertEqual(p["status"],"draft_unapproved")
 def test_negative_delta_yields_no_allocation(self):
  self.base["entries"][0]["amount"]="50000"
  c.import_entries(self.base)
  p=c.allocation_plan("KZT","2026-10-01","2026-10-31","20","80")
  self.assertEqual(p["investable_minor"],0)
  self.assertEqual(p["reserve_minor"],0)
 def test_missing_sources_denied(self):
  with self.assertRaisesRegex(ValueError,"NO_INPUT_SOURCES"):
   c.allocation_plan("KZT","2026-10-01","2026-10-31",20,50)
 def test_percent_guard(self):
  c.import_entries(self.base)
  for v in ["NaN","Infinity",-1,101,None]:
   with self.subTest(v=v):
    with self.assertRaises(ValueError):c.allocation_plan("KZT","2026-10-01","2026-10-31",v,50)
if __name__=="__main__":unittest.main()
