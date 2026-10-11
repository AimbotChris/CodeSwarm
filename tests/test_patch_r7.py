"""Patch safety tests in temporary fixture trees; no system installation."""
import importlib.util,pathlib,tempfile,unittest,hashlib
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('patcher',ROOT/'update-r7/install.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PatchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
  for name,relative in m.TARGETS.items():
   p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/'tests/fixtures/r6-connect'/name).read_bytes());p.chmod(0o755)
  # File operations are real in the private fixture; ownership walk is tested separately.
  self.guard=patch.object(m,'secure_path');self.guard.start()
 def tearDown(self):self.guard.stop();self.tmp.cleanup()
 def hashes(self):return {n:m.digest(self.root/r) for n,r in m.TARGETS.items()}
 def test_apply_and_restore_exact_bytes(self):
  before=self.hashes();m.change(self.root);self.assertNotEqual(before,self.hashes());m.change(self.root,True);self.assertEqual(before,self.hashes())
 def test_unknown_install_refused_without_backup_or_mutation(self):
  p=self.root/m.TARGETS['code-swarm-connect'];p.write_text('owner modification');before=self.hashes()
  with self.assertRaises(RuntimeError):m.change(self.root)
  self.assertEqual(before,self.hashes());self.assertFalse((self.root/m.BACKUP).exists())
 def test_partial_write_failure_restores_original_files(self):
  real=m.replace;calls=0;before=self.hashes()
  def fail_once(p,data):
   nonlocal calls
   calls+=1
   if calls==2:raise OSError('injected write failure')
   return real(p,data)
  with patch.object(m,'replace',side_effect=fail_once):
   with self.assertRaises(OSError):m.change(self.root)
  self.assertEqual(before,self.hashes())
 def test_modified_patch_restore_refused(self):
  m.change(self.root);(self.root/m.TARGETS['code-swarm-connect']).write_text('owner new change');before=self.hashes()
  with self.assertRaises(RuntimeError):m.change(self.root,True)
  self.assertEqual(before,self.hashes())
 def test_active_setup_refused_before_change(self):
  fake=type('P',(),{'read_bytes':lambda self:b'/usr/bin/python3\0/usr/local/bin/code-swarm-connect\0'})()
  with patch.object(m.os,'geteuid',return_value=0),patch.object(m.sys,'argv',['install.py']),patch.object(m.pathlib.Path,'glob',return_value=[fake]),patch.object(m,'change') as change:
   with self.assertRaises(RuntimeError):m.main()
   change.assert_not_called()
 def test_nonroot_rejected(self):
  with patch.object(m.os,'geteuid',return_value=1000),patch.object(m,'change') as change:
   with self.assertRaises(RuntimeError):m.main()
   change.assert_not_called()
if __name__=='__main__':unittest.main()
