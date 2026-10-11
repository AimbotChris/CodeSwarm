import importlib.machinery,importlib.util,pathlib,unittest,io,types
from unittest.mock import patch,MagicMock
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(name,file):
 loader=importlib.machinery.SourceFileLoader(name,str(ROOT/'product'/file));spec=importlib.util.spec_from_loader(name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m);return m
helper=load('connect_helper','code-swarm-tailscale-helper')
# UI state tests do not need a display; production widgets are exercised in the VM.
with patch.dict('sys.modules',{'tkinter':MagicMock(),'tkinter.ttk':MagicMock()}):ui=load('connect_ui','code-swarm-connect')
class ConnectTests(unittest.TestCase):
 def test_helper_rejects_unprivileged_and_extra_arguments(self):
  for uid,args in [(1000,['helper']),(0,['helper','arbitrary'])]:
   with patch.object(helper.os,'geteuid',return_value=uid),patch.object(helper.sys,'argv',args),patch.object(helper.subprocess,'run') as run:
    with self.assertRaises(SystemExit):helper.main()
    run.assert_not_called()
 def test_browser_allowlist(self):
  for m in (helper,ui):
   self.assertTrue(m.safe_url('https://login.tailscale.com/a/SYNTHETIC-NOT-A-REAL-LINK'))
   for url in ['http://login.tailscale.com/a/x','https://evil.example/a/x','https://login.tailscale.com.evil/a/x','https://user@ login.tailscale.com/a/x','https://login.tailscale.com:443/a/x','https://login.tailscale.com/a/x?secret=y','file:///tmp/x']:
    self.assertFalse(m.safe_url(url),url)
 def helper_run(self,states,cancel=False,after_start=False,timeout=False):
  events=[];selector=MagicMock();selector.select.return_value=[1] if cancel else []
  if after_start:selector.select.side_effect=[[],[1]]
  child=MagicMock();child.poll.return_value=None
  with patch.object(helper.os,'geteuid',return_value=0),patch.object(helper.sys,'argv',['helper']),patch('builtins.open',MagicMock()),patch.object(helper.os,'chmod'),patch.object(helper.os,'read',return_value=b''),patch.object(helper.time,'monotonic',side_effect=[0,126] if timeout else None,return_value=0),patch.object(helper.fcntl,'flock'),patch.object(helper.selectors,'DefaultSelector',return_value=selector),patch.object(helper,'status',side_effect=states),patch.object(helper.subprocess,'run') as run,patch.object(helper.subprocess,'Popen',return_value=child) as popen,patch.object(helper,'emit',side_effect=lambda *a,**kw:events.append((a,kw))):
   helper.main();return events,run,popen,child
 def test_cancel_before_service_change(self):
  e,r,p,c=self.helper_run([],True);r.assert_not_called();p.assert_not_called();self.assertEqual(e[-1][0][0],'cancelled')
 def test_cancel_after_service_start_cleans_child(self):
  e,r,p,c=self.helper_run([{'BackendState':'NeedsLogin'}],after_start=True);self.assertEqual(e[-1][0][0],'cancelled');c.terminate.assert_called_once()
 def test_timeout_cleans_child(self):
  e,r,p,c=self.helper_run([{'BackendState':'NeedsLogin'}],timeout=True);self.assertEqual(e[-1][0][0],'timeout');c.terminate.assert_called_once()
 def test_connected_no_login_or_settings_reset(self):
  e,r,p,c=self.helper_run([{'BackendState':'Running'}]);p.assert_not_called();self.assertEqual(e[-1][0][0],'connected')
 def test_existing_stopped_settings_not_overwritten(self):
  e,r,p,c=self.helper_run([{'BackendState':'Stopped','CurrentTailnet':{'Name':'qa'}}]);p.assert_not_called();self.assertEqual(e[-1][0][0],'failed')
 def test_initial_signin_then_real_status_connected(self):
  e,r,p,c=self.helper_run([{'BackendState':'NeedsLogin'},{'BackendState':'NeedsLogin','AuthURL':'https://login.tailscale.com/a/SYNTHETIC-NOT-A-REAL-LINK'},{'BackendState':'Running'}]);self.assertEqual([x[0][0] for x in e],['starting','connecting','signin','connected']);self.assertEqual(p.call_args.args[0],['/usr/bin/tailscale','up','--timeout=120s']);c.terminate.assert_called_once()
 def test_unexpected_auth_url_refused(self):
  e,r,p,c=self.helper_run([{'BackendState':'NeedsLogin'},{'BackendState':'NeedsLogin','AuthURL':'https://evil.example/a/x'}]);self.assertEqual(e[-1][0][0],'failed');self.assertTrue(all('url' not in x[1] for x in e));c.terminate.assert_called_once()
 def make_ui(self):
  obj=object.__new__(ui.Setup)
  for name in ('approve','browser','cancel_button','message','root','copy_button','link_text','qr_label','link_note'):setattr(obj,name,MagicMock())
  obj.waiting_admin=False;obj.copied_url=None;obj.link_deadline=10**15;obj.qr_image=None;obj.attempt=2;obj.running=True;obj.connected=False;obj.started=False;obj.closing=False;obj.process=None;obj.url=None
  return obj
 def test_old_approval_timeout_cannot_cancel_new_attempt(self):
  obj=self.make_ui();obj.process=MagicMock();obj.approval_timeout(1);obj.process.terminate.assert_not_called();obj.approval_timeout(2);obj.process.terminate.assert_called_once()
 def test_ui_approval_cancel_and_retry(self):
  obj=self.make_ui();obj.apply({'state':'ended','code':126});self.assertFalse(obj.running);self.assertIn('canceled or denied',obj.message.set.call_args.args[0]);self.assertEqual(obj.approve.configure.call_args.kwargs['state'],'normal')
 def test_ui_connected_does_not_offer_retry(self):
  obj=self.make_ui();obj.apply({'state':'connected','message':'Connected'});obj.apply({'state':'ended','code':0});self.assertEqual(obj.approve.configure.call_args.kwargs['state'],'disabled')
 def test_valid_signin_opens_only_user_firefox(self):
  obj=self.make_ui();obj.url='https://login.tailscale.com/a/SYNTHETIC-NOT-A-REAL-LINK'
  with patch.object(ui.subprocess,'Popen') as p:obj.open_browser();self.assertEqual(p.call_args.args[0],['/usr/bin/firefox-esr',obj.url])
 def test_ui_never_opens_untrusted_browser_url(self):
  obj=self.make_ui();obj.open_browser=MagicMock();obj.apply({'state':'signin','url':'https://evil.example/a/x'});obj.open_browser.assert_not_called()
 def test_ui_cancel_pending_prompt(self):
  obj=self.make_ui();obj.process=MagicMock();obj.cancel();self.assertTrue(obj.closing);obj.process.terminate.assert_called_once();obj.process.stdin.close.assert_called_once()
 def test_ui_failure_timeout_retry(self):
  for state in ('failed','timeout','cancelled'):
   obj=self.make_ui();obj.apply({'state':state,'message':'Try again'});obj.apply({'state':'ended','code':0});self.assertEqual(obj.approve.configure.call_args.kwargs['state'],'normal')
 def test_policy_and_explicit_package_contract(self):
  cfg=(ROOT/'scripts/configure.py').read_text();self.assertIn('user-setup\nsudo\nlxpolkit',cfg)
  policy=(ROOT/'scripts/polish-r6.py').read_text();self.assertIn('<allow_active>auth_admin</allow_active>',policy);self.assertNotIn('auth_admin_keep',policy);self.assertNotIn('NOPASSWD',policy)
if __name__=='__main__':unittest.main()
