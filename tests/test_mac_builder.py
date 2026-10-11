"""Synthetic fixtures only. No VM, credentials, enrollment or network requests."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'builder'/f'{name}.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result
m = module('mac'); f = module('firstboot'); p = module('personalize')
FAKE = 'tskey-auth-SYNTHETIC-NOT-A-REAL-KEY'

class MacBuilderTests(unittest.TestCase):
    def test_architecture(self):
        self.assertIn('emulation', m.architecture('Darwin','arm64'))
        self.assertIn('Intel', m.architecture('Darwin','x86_64'))
        for system,arch in [('Linux','x86_64'),('Darwin','aarch64'),('Darwin','i386')]:
            with self.assertRaises(RuntimeError): m.architecture(system,arch)
    def test_key_validation(self):
        self.assertTrue(m.valid_key(FAKE))
        for key in ['oauth-secret',FAKE+'\n',FAKE+';command',FAKE+' '+FAKE]:
            self.assertFalse(m.valid_key(key))
    def test_export_only_allowlisted_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'builder').mkdir(); (root/'product').mkdir()
            (root/'builder/source-files.txt').write_text('product/app\n')
            (root/'product/app').write_text('public source')
            for name in ['qa/password','vendor/app.deb','private/authkey','build/chroot/token','product/unlisted-key']:
                q=root/name; q.parent.mkdir(exist_ok=True,parents=True); q.write_text(FAKE)
            target=root/'export.tar'; m.archive(target,root)
            self.assertNotIn(FAKE.encode(),target.read_bytes())
            with tarfile.open(target) as tar: self.assertEqual(tar.getnames(),['product/app'])
    def test_export_rejects_symlink_and_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'builder').mkdir(); (root/'real').write_text('data')
            (root/'link').symlink_to(root/'real')
            for name in ['link','../elsewhere','/etc/passwd']:
                (root/'builder/source-files.txt').write_text(name+'\n')
                with self.assertRaises(RuntimeError): m.source_paths(root)
    def test_actual_manifest_has_no_runtime_files(self):
        names=[n for _,n in m.source_paths()]
        self.assertTrue(names)
        for name in names:
            self.assertFalse(set(Path(name).parts)&{'qa','vendor','private','build','.git','__pycache__'})
            self.assertNotIn(Path(name).suffix, {'.iso','.deb','.qcow2','.raw','.log'})
    def test_output_refuses_overwrite_and_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(RuntimeError):m.fresh_output(Path(temp))
        with self.assertRaises(RuntimeError):m.fresh_output(ROOT/'private-test-output')
    def test_rejects_low_resources_before_vm_mutation(self):
        with patch.object(m,'architecture',return_value='Intel'), patch.object(m.shutil,'which',return_value='/tool'), patch.object(m,'command',return_value=SimpleNamespace(stdout=str(4*m.GIB))):
            with self.assertRaises(RuntimeError):m.doctor(Path('/tmp/new-output'))
    def test_vm_has_no_host_mounts_or_agent(self):
        config=(ROOT/'builder/lima.yaml').read_text()
        for required in ['arch: x86_64','vmType: qemu','mounts: []','forwardAgent: false','plain: true','digest: sha512:']:
            self.assertIn(required,config)
    def test_concurrent_builder_refused(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(m,'STATE',Path(temp)):
            with m.builder_lock():
                with self.assertRaises(RuntimeError):
                    with m.builder_lock():self.fail('Concurrent builder admitted')
            with m.builder_lock():pass
    def test_stale_guest_helper_refused(self):
        with patch.object(m,'shell',return_value=SimpleNamespace(stdout='bad-digest  helper\n')):
            with self.assertRaises(RuntimeError):m.verify_private_helpers()
    def test_checksum_patch_replaces_only_changed(self):
        with tempfile.TemporaryDirectory() as temp:
            q=Path(temp)/'file';q.write_text('replacement')
            result=p.patch_checksums('abc  ./unchanged\nold  ./live/filesystem.squashfs\n',{'live/filesystem.squashfs':q},'md5')
            self.assertIn('abc  ./unchanged\n',result)
            self.assertIn(p.digest(q,'md5')+'  ./live/filesystem.squashfs',result)
            self.assertNotIn('old',result)

class FirstbootTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        for name in ['proc','var/lib/code-swarm','etc/code-swarm-enrollment']:(self.root/name).mkdir(parents=True,exist_ok=True)
        (self.root/'proc/cmdline').write_text('root=/dev/vda1 quiet')
        (self.root/'var/lib/code-swarm/admin-provisioned').write_text('ordinary-owner-password-required\n')
        self.key=self.root/'etc/code-swarm-enrollment/authkey';self.key.write_text(FAKE)
        self.stat=self.root/'var/lib/code-swarm/enrollment-status'
    def tearDown(self):self.temp.cleanup()
    def execute(self,state='Running'):
        with patch.object(f.os,'geteuid',return_value=0), patch.object(f,'secure_key',return_value=True), patch.object(f,'run',return_value=0) as run, patch.object(f.subprocess,'run',return_value=SimpleNamespace(stdout=json.dumps({'BackendState':state}).encode())):
            result=f.main(self.root)
            return result,run.call_args_list
    def test_installed_success_deletes_key_and_never_exposes_it_in_argv(self):
        result,calls=self.execute();self.assertEqual(result,0);self.assertFalse(self.key.exists())
        self.assertEqual(self.stat.read_text(),'connected\n')
        self.assertNotIn(FAKE,str(calls));self.assertIn('--auth-key=file:',str(calls))
    def test_device_approval_is_not_connected(self):
        self.assertEqual(self.execute('NeedsMachineAuth')[0],1)
        self.assertEqual(self.stat.read_text(),'pending-device-approval\n');self.assertFalse(self.key.exists())
    def test_live_boot_and_missing_owner_never_mutate_network(self):
        (self.root/'proc/cmdline').write_text('boot=live components')
        result,calls=self.execute();self.assertEqual(result,1);self.assertEqual(calls,[]);self.assertTrue(self.key.exists())
        (self.root/'proc/cmdline').write_text('root=/dev/vda1')
        (self.root/'var/lib/code-swarm/admin-provisioned').unlink()
        self.assertEqual(self.execute()[1],[])
    def test_existing_identity_is_never_reset(self):
        node=self.root/'var/lib/tailscale/tailscaled.state';node.parent.mkdir();node.write_text('synthetic-node-identity')
        self.assertEqual(self.execute()[1],[]);self.assertEqual(node.read_text(),'synthetic-node-identity');self.assertFalse(self.key.exists())
    def test_claim_blocks_retry_after_power_loss(self):
        self.stat.write_text('attempting\n')
        self.assertEqual(self.execute()[1],[]);self.assertFalse(self.key.exists())
    def test_timeout_deletes_key_and_fails_closed(self):
        with patch.object(f.os,'geteuid',return_value=0),patch.object(f,'secure_key',return_value=True),patch.object(f,'run',side_effect=f.subprocess.TimeoutExpired('synthetic',1)):
            self.assertEqual(f.main(self.root),1)
        self.assertFalse(self.key.exists());self.assertIn('failed-owner',self.stat.read_text())
    def test_insecure_permissions_refused(self):
        self.assertFalse(f.secure_key(self.key.parent,self.key))
    def test_service_bounded_and_no_secret_logs(self):
        service=(ROOT/'builder/configure-firstboot.py').read_text()
        for text in ['TimeoutStartSec=360','StandardOutput=null','StandardError=null','admin-provisioned','ConditionPathExists=!/run/live/medium']:
            self.assertIn(text,service)

if __name__ == '__main__':unittest.main()
