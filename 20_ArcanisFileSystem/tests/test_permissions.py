"""Tests for permission system."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from permissions.posix import PosixPermissions
from permissions.acl import ACL, ACLEntry, ACLPermission, ACLScope
from permissions.auth import Authenticator, User, Session


class TestPosixPermissions(unittest.TestCase):
    def test_default_permissions(self):
        perms = PosixPermissions()
        self.assertEqual(perms.mode, 0o644)

    def test_owner_permissions(self):
        perms = PosixPermissions(0o700)
        self.assertTrue(perms.owner_read)
        self.assertTrue(perms.owner_write)
        self.assertTrue(perms.owner_execute)
        self.assertFalse(perms.group_read)

    def test_to_symbolic(self):
        perms = PosixPermissions(0o755)
        symbolic = perms.to_symbolic()
        self.assertEqual(symbolic, "rwxr-xr-x")

    def test_check_read(self):
        perms = PosixPermissions(0o644)
        self.assertTrue(perms.check_read(1000, 1000, 1000, 1000))
        self.assertTrue(perms.check_read(1000, 1000, 1000, 1001))
        self.assertTrue(perms.check_read(1001, 1001, 1000, 1000))

        perms2 = PosixPermissions(0o600)
        self.assertTrue(perms2.check_read(1000, 1000, 1000, 1000))
        self.assertFalse(perms2.check_read(1001, 1001, 1000, 1000))

    def test_setuid(self):
        perms = PosixPermissions()
        perms.set_setuid(True)
        self.assertTrue(perms.is_setuid)


class TestACL(unittest.TestCase):
    def test_create_acl(self):
        acl = ACL()
        self.assertIsNotNone(acl.id)
        self.assertEqual(acl.count(), 0)

    def test_add_entry(self):
        acl = ACL()
        entry = ACLEntry(scope=ACLScope.EVERYONE, permissions=ACLPermission.READ)
        acl.add_entry(entry)
        self.assertEqual(acl.count(), 1)

    def test_check_permission(self):
        acl = ACL()
        entry = ACLEntry(scope=ACLScope.OWNER, permissions=ACLPermission.FULL_CONTROL)
        acl.add_entry(entry)
        result = acl.check_permission(1000, 1000, [1000], ACLPermission.READ, 1000, 1000)
        self.assertTrue(result)

    def test_deny_permission(self):
        acl = ACL()
        entry = ACLEntry(scope=ACLScope.OTHER, permissions=ACLPermission.NONE)
        acl.add_entry(entry)
        result = acl.check_permission(9999, 9999, [9999], ACLPermission.READ, 1000, 1000)
        self.assertFalse(result)

    def test_to_dict(self):
        acl = ACL()
        entry = ACLEntry(scope=ACLScope.EVERYONE, permissions=ACLPermission.READ)
        acl.add_entry(entry)
        d = acl.to_dict()
        self.assertIn("entries", d)


class TestAuthenticator(unittest.TestCase):
    def test_create_user(self):
        auth = Authenticator()
        user = auth.create_user("testuser", "password123")
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.verify_password("password123"))

    def test_authenticate(self):
        auth = Authenticator()
        auth.create_user("testuser", "password123")
        user = auth.authenticate("testuser", "password123")
        self.assertIsNotNone(user)

    def test_authenticate_wrong_password(self):
        auth = Authenticator()
        auth.create_user("testuser", "password123")
        user = auth.authenticate("testuser", "wrongpassword")
        self.assertIsNone(user)

    def test_session(self):
        auth = Authenticator()
        user = auth.create_user("testuser", "password123")
        session = auth.create_session(user)
        self.assertTrue(session.is_active())
        retrieved = auth.get_session(session.id)
        self.assertIsNotNone(retrieved)

    def test_root_user(self):
        auth = Authenticator()
        root = auth.get_user(0)
        self.assertIsNotNone(root)
        self.assertEqual(root.username, "root")

    def test_delete_user(self):
        auth = Authenticator()
        user = auth.create_user("testuser", "password123")
        self.assertTrue(auth.delete_user(user.id))

    def test_cannot_delete_root(self):
        auth = Authenticator()
        with self.assertRaises(PermissionError):
            auth.delete_user(0)


if __name__ == "__main__":
    unittest.main()
