import importlib.util,json,pathlib,time,unittest,multiprocessing
from unittest.mock import patch
import subprocess
spec=importlib.util.spec_from_file_location('fleet',pathlib.Path(__file__).resolve().parents[1]/'fleet/server.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FleetTests(unittest.TestCase):
 def setUp(self):
  self.peer={'HostName':'Mini PC','DNSName':'mini.example.ts.net.','Online':True}
  self.config={'mini.example.ts.net':{'desktop_url':'https://mini.example.ts.net/vnc.html','status_url':'https://mini.example.ts.net/code-swarm-status'}}
  self.status={'schema':1,'observed_at':1000,'desktop':'active','app':'running','same_session_vnc':True}
 def probe(self,url,method='GET'):return (401,b'') if method=='HEAD' else (200,json.dumps(self.status).encode())
 def row(self):return m.peer_row(self.peer,self.config,self.probe,1000)
 def test_fresh_password_gate(self):
  r=self.row();self.assertIsNotNone(r['desktop_url']);self.assertEqual(r['worker'],'unknown');self.assertEqual(r['app'],'running')
 def test_unconfigured(self):self.assertEqual(m.peer_row(self.peer,{})['desktop'],'unknown')
 def test_offline_no_probe(self):
  self.peer['Online']=False;r=self.row();self.assertIsNone(r['desktop_url']);self.assertEqual(r['app'],'unknown')
 def test_stale(self):
  self.status['observed_at']=100;r=self.row();self.assertEqual(r['telemetry'],'stale');self.assertIsNone(r['desktop_url']);self.assertEqual(r['app'],'unknown')
 def test_clock_future(self):self.status['observed_at']=1100;self.assertEqual(self.row()['telemetry'],'stale')
 def test_greeter(self):
  self.status['desktop']='needs-login';r=self.row();self.assertIsNotNone(r['desktop_url']);self.assertIn('login screen',r['detail'])
 def test_missing_display(self):
  self.status['desktop']='display-unavailable';r=self.row();self.assertIsNone(r['desktop_url']);self.assertIn('EDID',r['detail'])
 def test_no_session(self):self.status['desktop']='inactive';self.assertIsNone(self.row()['desktop_url'])
 def test_vnc_crashed(self):self.status['same_session_vnc']=False;self.assertIsNone(self.row()['desktop_url'])
 def test_app_is_not_work(self):self.status['app']='failed';r=self.row();self.assertEqual(r['app'],'failed');self.assertEqual(r['worker'],'unknown')
 def test_network_failure(self):
  def fail(*args):raise TimeoutError('Worker timed out')
  r=m.peer_row(self.peer,self.config,fail,1000);self.assertEqual(r['telemetry'],'error');self.assertEqual(r['app'],'unknown')
 def test_redirect_no_link(self):
  def redirected(url,method='GET'):return (302,b'') if method=='HEAD' else self.probe(url)
  self.assertIsNone(m.peer_row(self.peer,self.config,redirected,1000)['desktop_url'])
 def test_no_ssrf(self):
  for url in ['http://mini.example.ts.net/vnc.html','https://evil.ts.net/vnc.html','https://mini.example.ts.net:443/vnc.html','https://u:p@mini.example.ts.net/vnc.html','https://mini.example.ts.net/vnc.html?token=x','https://mini.example.ts.net/vnc.html#x','https://mini.example.ts.net/other']:
   with self.subTest(url=url):
    self.config['mini.example.ts.net']['desktop_url']=url;self.assertEqual(self.row()['telemetry'],'error')
 def test_reconnect(self):
  self.peer['Online']=False;self.assertIsNone(self.row()['desktop_url']);self.peer['Online']=True;self.assertIsNotNone(self.row()['desktop_url'])
 def test_aggregate_deadline_and_cleanup(self):
  peers=[dict(self.peer,ID=str(i)) for i in range(100)]
  before={p.pid for p in multiprocessing.active_children()}
  for _ in range(2):
   start=time.monotonic();rows=m.bounded_probes(peers,self.config,budget=.25,per_peer=.2,target=slow_probe)
   self.assertLess(time.monotonic()-start,1.5);self.assertEqual(len(rows),100);self.assertTrue(all(r['desktop_url'] is None for r in rows))
  self.assertEqual({p.pid for p in multiprocessing.active_children()},before)
 def test_no_refresh_queue(self):
  f=m.Fleet(pathlib.Path('/unused'));f.lock.acquire()
  try:
   start=time.monotonic();r=f.snapshot();self.assertLess(time.monotonic()-start,.1);self.assertIn('already in progress',r['error'])
  finally:f.lock.release()
class ConnectionTests(unittest.TestCase):
 def test_status_states(self):
  for backend,kind in [('NeedsLogin','not-logged-in'),('Stopped','not-running'),('NeedsMachineAuth','needs-approval'),('Starting','unavailable')]:
   with self.subTest(backend=backend), patch.object(m,'run_json',return_value={'BackendState':backend}):
    status,issue=m.tailscale_status();self.assertIsNone(status);self.assertEqual(issue['connection_state'],kind);self.assertEqual(issue['error'],m.CONNECTION_MESSAGES[kind][0])
 def test_missing_and_permissions(self):
  for error,kind in [(FileNotFoundError('missing'),'not-installed'),(PermissionError('denied'),'permission-denied'),(subprocess.CalledProcessError(1,['tailscale'],stderr='permission denied'),'permission-denied')]:
   with self.subTest(kind=kind), patch.object(m,'run_json',side_effect=error):
    self.assertEqual(m.tailscale_status()[1]['connection_state'],kind)
 def test_failed_command_requires_daemon_evidence(self):
  error=subprocess.CalledProcessError(1,['tailscale','status','--json'],stderr='cannot connect')
  for output,kind in [('LoadState=loaded\nActiveState=inactive\n','not-running'),('LoadState=not-found\nActiveState=inactive\n','unavailable'),('LoadState=loaded\nActiveState=active\n','unavailable')]:
   with self.subTest(output=output), patch.object(m,'run_json',side_effect=error),patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0,output,'')):
    issue=m.tailscale_status()[1];self.assertEqual(issue['connection_state'],kind);self.assertNotIn('Command',issue['error']);self.assertIn('cannot connect',issue['technical_detail'])
 def test_running(self):
  with patch.object(m,'run_json',return_value={'BackendState':'Running'}):self.assertIsNone(m.tailscale_status()[1])
def slow_probe(connection,peer,config):
 time.sleep(10)
if __name__=='__main__':unittest.main()
