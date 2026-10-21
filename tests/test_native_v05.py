import unittest, tempfile, json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import sync_smm_native as smm
from workspace import service

class NativeTests(unittest.TestCase):
 def test_missing_original_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   old=smm.SOURCE
   try:
    smm.SOURCE=Path(d)/'not_imported'
    with self.assertRaises(SystemExit):smm.sync()
   finally:smm.SOURCE=old
 def test_original_preserved_hashes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'original';dest=root/'out'/'smm';source.mkdir()
   (source/'index.html').write_bytes(b'<h1>Original</h1>')
   (source/'workspaces.html').write_bytes(b'<h1>Workspace</h1>')
   old_src,old_dest=smm.SOURCE,smm.DEST
   try:
    smm.SOURCE,smm.DEST=source,dest
    manifest=smm.sync()
    self.assertEqual((dest/'workspaces.html').read_bytes(),(source/'workspaces.html').read_bytes())
    self.assertTrue(manifest['cabinet_status']['workspaces.html'])
    self.assertFalse(manifest['cabinet_status']['studio.html'])
    self.assertEqual(json.loads((dest.parent/'smm-provenance.json').read_text())['files'],manifest['files'])
   finally:smm.SOURCE,smm.DEST=old_src,old_dest
 def test_no_provider_exec_even_if_approved(self):
  with tempfile.TemporaryDirectory() as d:
   old=service.DB
   try:
    service.DB=Path(d)/'a.db';service.connect().close()
    lead=service.create_lead('Local Example','avito');a=service.prepare_action(lead,'avito.message','draft')
    service.approve_action(a['id'])
    r=service.execute_action(a['id'])
    self.assertFalse(r['external_effects'])
    self.assertEqual(r['code'],'NO_VERIFIED_PROVIDER_ADAPTER')
    self.assertTrue(any(x['action']=='action.execute_denied' for x in service.list_data('audit')))
   finally:service.DB=old
if __name__=='__main__':unittest.main()
