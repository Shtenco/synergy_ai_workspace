import os,tempfile,unittest
from pathlib import Path
from workspace import service as s
class TestControlPlane(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();s.DB=Path(self.tmp.name)/'test.sqlite3'
 def tearDown(self):self.tmp.cleanup()
 def test_lifecycle(self):
  i=s.create_task('Post brief','smm');self.assertEqual(s.list_data('tasks')[0]['status'],'draft')
  s.update_task(i,'review');s.update_task(i,'approved');s.update_task(i,'done')
  self.assertEqual(len(s.list_data('audit')),4)
 def test_guard(self):
  with self.assertRaises(ValueError):s.create_task('x','unknown')
  i=s.create_task('x','avito')
  with self.assertRaises(ValueError):s.update_task(i,'done')
 def test_crm(self):
  s.create_lead('Client','avito');self.assertEqual(s.list_data('leads')[0]['source'],'avito')
if __name__=='__main__':unittest.main()
