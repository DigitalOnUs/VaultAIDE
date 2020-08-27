import docker
import subprocess
import time
import os
import unittest
import re

from vault import Vault
from logging import debug

class TestIntegrationVault(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.addr = "http://localhost:8200"
        self.token = "root"

        os.environ['VAULT_ADDR'] = self.addr
        os.environ['VAULT_TOKEN'] = self.token

        self.v = Vault(self.addr, self.token)

        # Setup docker
        self.container = docker.from_env().containers.run(
            'vault',
            'vault server -dev -dev-root-token-id="root" -dev-listen-address="0.0.0.0:8200"',
            detach=True,
            remove=True,
            name='vault',
            ports={'8200':'8200'}
        )

        # Wait a second for docker
        # Change to the provisioner directory and run it
        time.sleep(1)
        p = subprocess.Popen(["python", "vault_api_provisioner.py", "--log=Debug"], cwd="vault-api-provisioner")
        p.wait()

    @classmethod
    def tearDownClass(self):
        # Clean up docker
        self.container.stop()

    def setUp(self):
        # This magically auth to Vault with the token
        self.v.client.token = self.token

    def tearDown(self):
        self.logoutFromVault()

    def logoutFromVault(self):
        self.v.client.logout()

    # Integration Tests
    def test_is_authenticated(self):
        # True case
        self.assertTrue(self.v.is_authenticated())

        # False case
        self.logoutFromVault()
        self.assertFalse(self.v.is_authenticated())

    def test_get_status(self):
        # JSON Case
        response = self.v.get_status()
        initialized = response.get('initialized')

        self.assertTrue(initialized)

        # None Case
        self.logoutFromVault()
        response = self.v.get_status()

        self.assertIsNone(response)

    def test_get_identity(self):
        identity = self.v.get_identity()
        id = identity.get('id')

        # We are querying with a root token
        self.assertEqual(id, 'root')

    def test_is_root(self):
        self.assertTrue(self.v.is_root())

    def test_is_initialized(self):
        self.assertTrue(self.v.is_initialized())

    def test_get_policies(self):
        response = self.v.get_policies()
        self.assertIsInstance(response, list)
        self.assertIn("root", response)

    def test_get_audit_devices(self):
        # We are testing against to stdout
        response = self.v.get_audit_devices()
        typ = response.get('stdout/')

        self.assertIsNotNone(typ)

    def test_get_metrics(self):
        # We are testing against to stdout
        response = self.v.get_metricts()
        typ = response.get('Gauges')

        self.assertIsNotNone(typ)

    # def test_get_expire_leases(self):
        # # Create tokens with different leases times
        # for t in ['6h', '9h', '4h', '5h', '1h', '30m', '76h', '8h']:
            # test = self.v.client.create_token(lease=t)

    def test_get_configuration(self):
        self.assertIsNotNone(self.v.get_configuration())

    def test_get_health(self):
        response = self.v.get_health()
        initialized = response.get('initialized')
        sealed = response.get('sealed')

        self.assertTrue(initialized)
        self.assertFalse(sealed)

    def test_get_general_information(self):
        self.assertIsNotNone(self.v.get_general_information())

    def test_get_version(self):
        versionPattern = r'\d+(=?\.(\d+(=?\.(\d+)*)*)*)*'
        regexMatcher = re.compile(versionPattern)

        self.assertIsNotNone(regexMatcher.match(self.v.get_version()))

    # def test_get_features(self):
        # debug(self.v.get_features())

    def test_integrated_app(self):
        self.assertIsNotNone(self.v.get_integrated_apps())

    # def test_wrapping(self):
        # debug(self.v.wrapping('test'))

    # def test_get_roles(self):
        # debug(self.v.get_roles())

    # This has problems with a TinyDB dependency
    # def test_overall_week(self):
        # debug(self.v.get_overall_week())

    def test_get_secrets_engine_list(self):
        self.assertIsNotNone(self.v.get_secrets_engine_list())

    def test_get_auth_methods(self):
        self.assertIsNotNone(self.v.get_auth_methods())

    def test_get_total_entities_count(self):
        self.assertIsNotNone(self.v.get_total_entities_count())

    def test_get_total_roles(self):
        self.assertGreaterEqual(self.v.get_total_roles(), 0)

    def test_get_total_tokens(self):
        self.assertGreaterEqual(self.v.get_total_tokens(), 1)

    def test_get_total_leases(self):
        self.assertGreaterEqual(self.v.get_total_leases(), 1)

    def test_get_leases_detail(self):
        for k, v in self.v.get_leases_detail().items():
            if k == 'non_renewable' or k == 'infinite_ttl':
                self.assertEqual(v, 1)
                continue

            if k == 'shortest' or k == 'longest':
                self.assertEqual(v, '')
                continue

            if k == 'shortest_ttl':
                self.assertIsNone(v)
                continue

            self.assertEqual(v, 0)

    # def test_unused_resources_watch(self):
        # debug(self.v.unused_resources_watch())

    # def test_vault_posture_score(self):
        # debug(self.v.vault_posture_score())

if __name__ == '__main__':
    unittest.main()
