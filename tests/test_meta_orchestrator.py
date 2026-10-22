"""META-API compatible local bridge: read-only and draft financial operations only."""
import tempfile,unittest
from pathlib import Path
from workspace import service,capital_engine as finance,meta_orchestrator as orchestrator

class TestOrchestrator(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();service.DB=Path(self.tmp.name)/"control.sqlite3"
  finance.import_entries({"source_id":"manual:oct26","currency":"KZT","period_start":"2026-10-01","period_end":"2026-10-31",
   "entries":[{"entry_id":"a","date":"2026-10-01","kind":"income","amount":"500000.00"},{"entry_id":"b","date":"2026-10-02","kind":"expense","amount":"300000.00"}]})
 def tearDown(self):self.tmp.cleanup()
 def test_local_finance_workflow(self):
  result=orchestrator.run([
   {"capability":"workspace.tasks.list"},
   {"capability":"workspace.capital.summary","arguments":{"currency":"KZT","start":"2026-10-01","end":"2026-10-31"}},
   {"capability":"workspace.capital.allocate.plan","arguments":{"currency":"KZT","start":"2026-10-01","end":"2026-10-31","reserve_pct":20,"investment_pct":50}}
  ])
  self.assertEqual(result["status"],"completed_local")
  self.assertFalse(result["external_effects"])
  self.assertFalse(result["provider_actions"])
  self.assertEqual(result["results"][1]["result"]["delta_minor"],20000000)
  self.assertEqual(result["results"][2]["result"]["investable_minor"],8000000)
  self.assertEqual(len(result["receipt_sha256"]),64)
 def test_reject_external_whole_workflow_before_running(self):
  before=len(service.list_data("audit"))
  with self.assertRaises(PermissionError):
   orchestrator.run([{"capability":"workspace.capital.allocate.plan","arguments":{"currency":"KZT"}},{"capability":"external.investment.trade","arguments":{}}])
  self.assertEqual(len(service.list_data("audit")),before)
 def test_unknown_dynamic_tool_denied(self):
  with self.assertRaises(PermissionError):orchestrator.run([{"capability":"shell.exec","arguments":{"command":"whoami"}}])
 def test_catalog_blocks_external(self):
  caps=orchestrator.list_capabilities()
  self.assertFalse(caps["meta_api_live_connected"])
  self.assertFalse(caps["external_execution"])
  self.assertTrue(any(c["effect"]=="blocked" for c in caps["capabilities"]))
if __name__=="__main__":unittest.main()
