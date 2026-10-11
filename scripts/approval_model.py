"""Pure prototype policy model, NOT an update executor or trusted OS boundary.
Production integration must reside behind root-owned control storage and an
independent control principal, never the desktop/workload UID. No live API.
"""
import hashlib,json,threading

def digest(m):return hashlib.sha256(json.dumps(m,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class Gate:
 def __init__(self,device):
  self.device=device;self.lock=threading.Lock();self.admission=True;self.jobs=set();self.spent=set();self.state='pending';self.maintenance=False
 def admit(self,job):
  with self.lock:
   if not self.admission: return False
   self.jobs.add(job);return True
 def finish(self,job):
  with self.lock:self.jobs.discard(job)
 def review(self,m,p,now,*,principal='workload',unmanaged=True,cgroups_empty=False,lifecycle_verified=False):
  with self.lock:
   if principal!='control':return 'unauthorized'
   if not p:return 'pending'
   if p.get('device')!=self.device or m.get('device')!=self.device:return 'wrong-device'
   if p.get('manifest')!=digest(m):return 'changed-manifest'
   if not isinstance(p.get('expires'),int) or not now < p['expires'] <= now+900:return 'expired-or-unbounded'
   nonce=p.get('nonce')
   if not isinstance(nonce,str) or len(nonce)<16 or nonce in self.spent:return 'replayed-or-invalid'
   # Atomically close admission before examining controlled registry/cgroups.
   self.admission=False
   if self.jobs or not cgroups_empty or unmanaged or not lifecycle_verified:
    self.admission=True;self.state='deferred';return self.state
   self.spent.add(nonce);self.maintenance=True;self.state='approved-no-executor'
   return self.state
