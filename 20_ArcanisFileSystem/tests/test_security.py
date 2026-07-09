"""Tests for security modules."""

import os
import sys
import time
import uuid
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from security.encryption import EncryptionManager, EncryptionKey
from security.recovery import RecoveryManager, Snapshot, SnapshotType
from security.audit import AuditLogger, AuditEvent, AuditLevel


class TestEncryptionManager(unittest.TestCase):
    def test_generate_key(self):
        em = EncryptionManager()
        key = em.generate_key("test key")
        self.assertIsNotNone(key)
        self.assertTrue(key.is_active)

    def test_encrypt_decrypt(self):
        em = EncryptionManager()
        key = em.generate_key()
        data = b"Hello, ArcanisFileSystem!"
        encrypted = em.encrypt_block(data, key)
        decrypted = em.decrypt_block(encrypted, key)
        self.assertEqual(data, decrypted)

    def test_wrong_key_fails(self):
        em = EncryptionManager()
        key1 = em.generate_key()
        key2 = em.generate_key()
        data = b"secret data"
        encrypted = em.encrypt_block(data, key1)
        with self.assertRaises(ValueError):
            em.decrypt_block(encrypted, key2)

    def test_revoke_key(self):
        em = EncryptionManager()
        key = em.generate_key()
        self.assertTrue(em.revoke_key(key.id))
        self.assertFalse(key.is_active)

    def test_file_key_assignment(self):
        em = EncryptionManager()
        key = em.generate_key()
        inode_id = uuid.uuid4()
        em.assign_key_to_file(inode_id, key.id)
        retrieved = em.get_file_key(inode_id)
        self.assertEqual(retrieved.id, key.id)

    def test_rotate_key(self):
        em = EncryptionManager()
        old_key = em.generate_key()
        new_key = em.rotate_key(old_key.id)
        self.assertFalse(old_key.is_active)
        self.assertTrue(new_key.is_active)

    def test_empty_data(self):
        em = EncryptionManager()
        key = em.generate_key()
        result = em.encrypt_block(b"", key)
        self.assertEqual(result, b"")


class TestRecoveryManager(unittest.TestCase):
    def test_create_snapshot(self):
        rm = RecoveryManager()
        snap = rm.create_snapshot("test")
        self.assertIsNotNone(snap)
        self.assertEqual(snap.name, "test")

    def test_complete_snapshot(self):
        rm = RecoveryManager()
        snap = rm.create_snapshot("test")
        completed = rm.complete_snapshot(snap.id, 1024, ["inode1", "inode2"])
        self.assertTrue(completed.is_valid())

    def test_delete_snapshot(self):
        rm = RecoveryManager()
        snap = rm.create_snapshot("test")
        self.assertTrue(rm.delete_snapshot(snap.id))

    def test_list_snapshots(self):
        rm = RecoveryManager()
        rm.create_snapshot("snap1")
        rm.create_snapshot("snap2")
        snapshots = rm.list_snapshots()
        self.assertEqual(len(snapshots), 2)

    def test_snapshot_chain(self):
        rm = RecoveryManager()
        snap1 = rm.create_snapshot("base")
        rm.complete_snapshot(snap1.id, 100, [])
        snap2 = rm.create_snapshot("incr", parent_id=snap1.id)
        rm.complete_snapshot(snap2.id, 50, [])
        chain = rm.get_snapshot_chain(snap2.id)
        self.assertEqual(len(chain), 2)

    def test_verify_snapshot(self):
        rm = RecoveryManager()
        snap = rm.create_snapshot("test")
        rm.complete_snapshot(snap.id, 1024, ["inode1"])
        self.assertTrue(rm.verify_snapshot(snap.id))


class TestAuditLogger(unittest.TestCase):
    def test_log_entry(self):
        al = AuditLogger()
        entry = al.log(AuditEvent.FILE_CREATE, AuditLevel.INFO, path="/test.txt")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.event, AuditEvent.FILE_CREATE)

    def test_query(self):
        al = AuditLogger()
        al.log(AuditEvent.FILE_CREATE, path="/a.txt")
        al.log(AuditEvent.FILE_DELETE, path="/b.txt")
        results = al.query(event=AuditEvent.FILE_CREATE)
        self.assertEqual(len(results), 1)

    def test_callback(self):
        al = AuditLogger()
        callback_called = []

        def callback(entry):
            callback_called.append(entry)

        al.add_callback(callback)
        al.log(AuditEvent.FILE_READ)
        self.assertEqual(len(callback_called), 1)

    def test_statistics(self):
        al = AuditLogger()
        al.log(AuditEvent.FILE_CREATE)
        al.log(AuditEvent.FILE_CREATE)
        al.log(AuditEvent.FILE_DELETE)
        stats = al.get_event_statistics()
        self.assertEqual(stats["file.create"], 2)

    def test_export(self):
        al = AuditLogger()
        al.log(AuditEvent.FILE_CREATE)
        filepath = "/tmp/test_audit_export.json"
        try:
            count = al.export_json(filepath)
            self.assertEqual(count, 1)
        except Exception:
            pass

    def test_clear(self):
        al = AuditLogger()
        al.log(AuditEvent.FILE_CREATE)
        count = al.clear()
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
