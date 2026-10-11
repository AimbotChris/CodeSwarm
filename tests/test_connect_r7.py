"""Only synthetic non-credential URLs. Never run an authentication request."""
import test_connect_r6 as base
helper=base.helper
ui=base.ui
from unittest.mock import patch,MagicMock
import unittest

LINK='https://login.tailscale.com/a/SYNTHETIC-NOT-A-REAL-LINK'
NEXT='https://login.tailscale.com/a/SYNTHETIC-ROTATED-LINK'
class LinkTests(unittest.TestCase):
 def make_ui(self):return base.ConnectTests().make_ui()
 def test_strict_official_url(self):
  for m in (helper,ui):
   self.assertTrue(m.safe_url(LINK))
   for bad in [None,1,{},LINK+'\n',LINK+' ',LINK+'?x=1',LINK+'#x',LINK+'/extra','https://login.tailscale.com/a/','https://login.tailscale.com:443/a/a','https://evil@ login.tailscale.com/a/a','https://login.tailscale.com/a/%0a','https://login.tailscale.com/a/'+'a'*257]:self.assertFalse(m.safe_url(bad))
 def test_signin_is_visible_but_never_auto_opens_browser(self):
  o=self.make_ui()
  with patch.object(ui.subprocess,'Popen') as p:
   o.apply({'state':'signin','url':LINK});p.assert_not_called()
  self.assertEqual(o.url,LINK);o.link_text.insert.assert_called_with('1.0',LINK)
  self.assertEqual(o.copy_button.configure.call_args.kwargs['state'],'normal')
 def test_copy_uses_current_link(self):
  o=self.make_ui();o.show_link(LINK);o.copy_link();o.root.clipboard_append.assert_called_once_with(LINK)
 def test_stale_link_cannot_copy_or_open(self):
  o=self.make_ui();o.url=LINK;o.link_deadline=0
  with patch.object(ui.subprocess,'Popen') as p:o.copy_link();o.open_browser();p.assert_not_called()
  o.root.clipboard_append.assert_not_called();self.assertIsNone(o.url)
 def test_rotation_clears_only_owned_clipboard(self):
  o=self.make_ui();o.show_link(LINK);o.copy_link();o.root.clipboard_get.return_value=LINK;o.root.clipboard_clear.reset_mock()
  o.show_link(NEXT);o.root.clipboard_clear.assert_called_once();self.assertEqual(o.url,NEXT)
 def test_clear_does_not_erase_unrelated_clipboard(self):
  o=self.make_ui();o.copied_url=LINK;o.root.clipboard_get.return_value='owner unrelated text';o.clear_link();o.root.clipboard_clear.assert_not_called()
 def test_all_terminal_and_withdrawal_states_clear_link(self):
  for state in ['waiting','approval','connected','failed','cancelled','timeout','ended']:
   o=self.make_ui();o.show_link(LINK);o.apply({'state':state,'code':0});self.assertIsNone(o.url,state);self.assertEqual(o.copy_button.configure.call_args.kwargs['state'],'disabled')
 def test_admin_approval_is_not_connected(self):
  o=self.make_ui();o.apply({'state':'approval'});self.assertFalse(o.connected)
 def test_old_attempt_and_after_cancel_events_cannot_restore_link(self):
  o=self.make_ui();o.apply({'state':'signin','url':LINK,'attempt':1});self.assertIsNone(o.url)
  o.cancel();o.apply({'state':'signin','url':LINK,'attempt':2});self.assertIsNone(o.url)
 def test_heartbeat_refreshes_freshness_without_redrawing(self):
  o=self.make_ui()
  with patch.object(ui.time,'monotonic',return_value=10):o.show_link(LINK)
  o.link_text.insert.reset_mock()
  with patch.object(ui.time,'monotonic',return_value=15):o.show_link(LINK)
  self.assertEqual(o.link_deadline,23);o.link_text.insert.assert_not_called()
 def test_missing_link_then_new_link_events(self):
  e,r,p,c=base.ConnectTests().helper_run([{'BackendState':'NeedsLogin'},{'BackendState':'NeedsLogin','AuthURL':LINK},{'BackendState':'NeedsLogin'},{'BackendState':'Running'}])
  self.assertEqual([x[0][0] for x in e],['starting','connecting','signin','waiting','connected'])
 def test_admin_approval_polled_until_running(self):
  e,r,p,c=base.ConnectTests().helper_run([{'BackendState':'NeedsMachineAuth'},{'BackendState':'NeedsMachineAuth'},{'BackendState':'Running'}]);p.assert_not_called()
  self.assertEqual([x[0][0] for x in e],['starting','approval','connected'])
 def test_link_rotation_and_admin_transition(self):
  e,r,p,c=base.ConnectTests().helper_run([{'BackendState':'NeedsLogin'},{'BackendState':'NeedsLogin','AuthURL':LINK},{'BackendState':'NeedsLogin','AuthURL':NEXT},{'BackendState':'NeedsMachineAuth'},{'BackendState':'Running'}])
  self.assertEqual([x[0][0] for x in e],['starting','connecting','signin','signin','approval','connected'])
 def test_pending_admin_refresh_needs_no_new_privilege(self):
  o=self.make_ui();o.running=False;o.waiting_admin=True;o.check=MagicMock()
  with patch.object(ui.subprocess,'Popen') as p:o.start();p.assert_not_called()
  o.check.assert_called_once()
 def test_connected_only_real_backend_running(self):
  e,r,p,c=base.ConnectTests().helper_run([{'BackendState':'NeedsLogin'}],timeout=True)
  self.assertNotIn('connected',[x[0][0] for x in e])
if __name__=='__main__':unittest.main()
