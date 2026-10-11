"""Official-source boundary tests, run in Debian image with python3-apt."""
import runpy,unittest,pathlib
from types import SimpleNamespace as N
covered=runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1]/'product/code-swarm-inventory'))['covered']
def candidate(site,origin='',trusted=True):return N(origins=[N(site=site,origin=origin,trusted=trusted)])
class Coverage(unittest.TestCase):
 def test_debian_signed(self):self.assertTrue(covered('later-installed-tool',candidate('deb.debian.org','Debian')))
 def test_unsigned_rejected(self):self.assertFalse(covered('chatgpt',candidate('persistent.oaistatic.com',trusted=False)))
 def test_unreviewed_signed_repo_rejected(self):self.assertFalse(covered('later-installed-tool',candidate('third-party.example','Debian')))
 def test_vendor_cannot_supply_os_packages(self):self.assertFalse(covered('systemd',candidate('persistent.oaistatic.com')))
 def test_vendor_package_allowed(self):self.assertTrue(covered('chatgpt',candidate('persistent.oaistatic.com')))
 def test_tailscale_scoped(self):self.assertTrue(covered('tailscale',candidate('pkgs.tailscale.com')));self.assertFalse(covered('bash',candidate('pkgs.tailscale.com')))
 def test_missing_candidate(self):self.assertFalse(covered('removed',None))
if __name__=='__main__':unittest.main()
