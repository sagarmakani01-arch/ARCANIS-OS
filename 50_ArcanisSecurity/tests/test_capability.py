import time

import pytest

from arcanis_security.capability import Capability, CapabilityScope, CapabilityToken
from arcanis_security.manager import CapabilityManager, SecurityPolicy, AuditLog


class TestCapabilityToken:
    def test_create_token(self):
        token = CapabilityToken(
            capability=Capability.FILE_READ,
            subject_id="process-1",
            resource_pattern="/tmp/*",
        )
        assert token.is_valid()
        assert token.capability == Capability.FILE_READ

    def test_expiry(self):
        token = CapabilityToken(
            capability=Capability.FILE_READ,
            subject_id="p1",
            expires_at=time.time() - 1,
        )
        assert not token.is_valid()

    def test_max_uses(self):
        token = CapabilityToken(
            capability=Capability.FILE_WRITE,
            subject_id="p1",
            max_uses=2,
        )
        assert token.consume()
        assert token.consume()
        assert not token.consume()

    def test_revoke(self):
        token = CapabilityToken(capability=Capability.ALL, subject_id="p1")
        token.revoked = True
        assert not token.is_valid()

    def test_resource_matching(self):
        token = CapabilityToken(
            capability=Capability.FILE_READ,
            subject_id="p1",
            resource_pattern="/tmp/",
        )
        assert token.matches_resource("/tmp/test.py")
        assert not token.matches_resource("/etc/passwd")

    def test_delegate(self):
        parent = CapabilityToken(
            capability=Capability.FILE_READ,
            subject_id="p1",
            resource_pattern="/tmp/",
        )
        child = parent.delegate(Capability.FILE_READ, "/tmp/sub/", expires_in=60)
        assert child.parent_token_id == parent.token_id
        assert child.is_valid()
        assert child.constraints.get("delegated") is True


class TestCapabilityManager:
    def setup_method(self):
        self.mgr = CapabilityManager()

    def test_grant_and_authorize(self):
        token = self.mgr.grant(Capability.FILE_READ, "user1", "/tmp/*")
        assert self.mgr.authorize(token.token_id, "read", "/tmp/test.py")

    def test_deny_revoked(self):
        token = self.mgr.grant(Capability.FILE_WRITE, "user1")
        self.mgr.revoke(token.token_id)
        assert not self.mgr.authorize(token.token_id, "write", "/tmp/x.py")

    def test_policy_deny(self):
        policy = SecurityPolicy()
        policy.add_deny(Capability.FILE_DELETE, "/important/")
        mgr = CapabilityManager(policy=policy)
        token = mgr.grant(Capability.FILE_DELETE, "user1", "/important/*")
        assert not mgr.authorize(token.token_id, "delete", "/important/secret.py")

    def test_delegate_chain(self):
        parent = self.mgr.grant(Capability.FILE_READ, "user1", "/tmp/*")
        child = self.mgr.delegate(parent.token_id, Capability.FILE_READ, "/tmp/sub/*")
        assert child is not None
        assert self.mgr.authorize(child.token_id, "read", "/tmp/sub/file.py")

    def test_audit_log(self):
        token = self.mgr.grant(Capability.FILE_READ, "user1")
        self.mgr.authorize(token.token_id, "read", "/tmp/x")
        entries = self.mgr.audit.query()
        assert len(entries) == 1
        assert entries[0]["granted"] is True

    def test_cleanup_expired(self):
        t1 = self.mgr.grant(Capability.FILE_READ, "u1", expires_in=-1)
        t2 = self.mgr.grant(Capability.FILE_READ, "u2", expires_in=3600)
        cleaned = self.mgr.cleanup_expired()
        assert cleaned == 1

    def test_get_active_tokens(self):
        self.mgr.grant(Capability.FILE_READ, "u1", expires_in=-1)
        self.mgr.grant(Capability.FILE_READ, "u2", expires_in=3600)
        active = self.mgr.get_active_tokens("u2")
        assert len(active) == 1


class TestSecurityPolicy:
    def test_deny_rule(self):
        policy = SecurityPolicy()
        policy.add_deny(Capability.NET_CONNECT, "external")
        token = CapabilityToken(capability=Capability.NET_CONNECT, subject_id="p1")
        assert not policy.check(token, "external-api.com")

    def test_allow_rule(self):
        policy = SecurityPolicy()
        policy.add_allow(Capability.FILE_READ, "/safe/")
        token = CapabilityToken(capability=Capability.FILE_READ, subject_id="p1")
        assert policy.check(token, "/safe/file.txt")

    def test_rate_limit(self):
        policy = SecurityPolicy()
        policy.set_rate_limit(Capability.AI_INFER, 2)
        token = CapabilityToken(capability=Capability.AI_INFER, subject_id="p1")
        mgr = CapabilityManager(policy=policy)
        assert mgr.authorize(token.token_id, "infer", "model")
        assert mgr.authorize(token.token_id, "infer", "model")
        assert not mgr.authorize(token.token_id, "infer", "model")


class TestAuditLog:
    def test_query(self):
        log = AuditLog()
        token = CapabilityToken(capability=Capability.FILE_READ, subject_id="u1")
        log.record("read", token, "/tmp/x", True)
        log.record("write", token, "/tmp/y", False)
        assert len(log.query(granted=True)) == 1
        assert len(log.query(granted=False)) == 1

    def test_stats(self):
        log = AuditLog()
        t1 = CapabilityToken(capability=Capability.FILE_READ, subject_id="u1")
        t2 = CapabilityToken(capability=Capability.FILE_WRITE, subject_id="u1")
        log.record("read", t1, "/a", True)
        log.record("write", t2, "/b", False)
        stats = log.stats()
        assert stats["total"] == 2
        assert stats["granted"] == 1
