import unittest
from mock import MagicMock
from vault import Vault

class TestVault(unittest.TestCase):
    v = Vault("http://0.0.0.0:8200", "fake token")
    commonIdentityResponse = dict({
        "path": "",
        "policies": [],
    })
    rootIdentityResponse = dict({
        "path": "auth/token/root",
        "policies": [
            "root"
        ],
    })

    def test_cleanup_json(self):
        data = {
            'a': None,
            'b': '',
            'c': 'c',
            'd': 'd',
            'e': 1,
            'f': dict(a='a', b='b'),
            'g': [1,2,3]
        }

        expected = {
            'c': 'c',
            'd': 'd',
            'e': 1,
            'f': dict(a='a', b='b'),
            'g': [1,2,3]
        }

        self.assertEqual(self.v.cleanup_json(data), expected)

    def test_is_authenticated(self):
        # True case
        self.v.is_authenticated = MagicMock(return_value=True)
        self.assertTrue(self.v.is_authenticated())

        # False case
        self.v.is_authenticated = MagicMock(return_value=False)
        self.assertFalse(self.v.is_authenticated())

    def test_get_status(self):
        response = {
            "initialized": True,
            "sealed": False,
            "standby": False,
            "performance_standby": False,
            "replication_perf_mode": "disabled",
            "replication_dr_mode": "disabled",
            "server_time_utc": 1516639589,
            "version": "0.9.1",
            "cluster_name": "vault-cluster-3bd69ca2",
            "cluster_id": "00af5aa8-c87d-b5fc-e82e-97cd8dfaf731"
        }

        # JSON case
        self.v.get_status = MagicMock(return_value=response)
        self.assertEqual(self.v.get_status(), response)

        # None case
        self.v.get_status = MagicMock(return_value=None)
        self.assertIsNone(self.v.get_status())

    def test_get_identity(self):
        self.v.get_identity = MagicMock(return_value=self.rootIdentityResponse)
        self.assertEqual(self.v.get_identity(), self.rootIdentityResponse)

    def test_is_root(self):
        self.v.get_identity = MagicMock(return_value=self.rootIdentityResponse)
        self.assertTrue(self.v.is_root())

        self.v.get_identity = MagicMock(return_value=self.commonIdentityResponse)
        self.assertFalse(self.v.is_root())

    def test_get_audit_devices(self):
        response = {
            "file": {
                "type": "file",
                "description": "Store logs in a file",
                "options": {
                    "file_path": "/var/log/vault.log"
                }
            }
        }

        self.v.get_audit_devices = MagicMock(return_value=response)
        self.assertEqual(self.v.get_audit_devices(), response)

    def test_is_initialized(self):
        self.v.is_initialized = MagicMock(return_value=False)
        self.assertFalse(self.v.is_initialized())

        self.v.is_initialized = MagicMock(return_value=True)
        self.assertTrue(self.v.is_initialized())

    def test_get_policies(self):
        response = ["root", "my-policy"]

        self.v.get_policies = MagicMock(return_value=response)
        self.assertEqual(self.v.get_policies(), response)

if __name__ == '__main__':
    unittest.main()
