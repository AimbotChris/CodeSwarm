import unittest,sys
sys.path.insert(0,'scripts')
from approval_model import Gate,digest
class Tests(unittest.TestCase):
 def setUp(self):
  self.g=Gate('test-device');self.m={'device':'test-device','packages':[{'version':'1'}]}
  self.p={'device':'test-device','manifest':digest(self.m),'expires':1100,'nonce':'unique-nonce-00001'}
 def check(self,p=None,**kw):
  return self.g.review(self.m,self.p if p is None else p,1000,principal='control',**kw)
 def test_pending(self):self.assertEqual(self.g.review(self.m,None,1000,principal='control'),'pending')
 def test_expired(self):self.p['expires']=999;self.assertEqual(self.check(),'expired-or-unbounded')
 def test_changed(self):self.m['packages'][0]['version']='2';self.assertEqual(self.check(),'changed-manifest')
 def test_device(self):self.p['device']='other';self.assertEqual(self.check(),'wrong-device')
 def test_unmanaged(self):self.assertEqual(self.check(cgroups_empty=True,lifecycle_verified=True),'deferred')
 def test_unverified_desktop(self):self.assertEqual(self.check(unmanaged=False,cgroups_empty=True),'deferred')
 def test_workload_cannot_permit(self):self.assertEqual(self.g.review(self.m,self.p,1000),'unauthorized')
 def test_active_job(self):self.g.admit('job');self.assertEqual(self.check(unmanaged=False,cgroups_empty=True,lifecycle_verified=True),'deferred')
 def test_cgroup(self):self.assertEqual(self.check(unmanaged=False,lifecycle_verified=True),'deferred')
 def test_single_use_and_admission(self):
  self.assertEqual(self.check(unmanaged=False,cgroups_empty=True,lifecycle_verified=True),'approved-no-executor')
  self.assertFalse(self.g.admit('race'));self.assertTrue(self.g.maintenance)
  self.assertEqual(self.check(),'replayed-or-invalid')
if __name__=='__main__':unittest.main(verbosity=2)
