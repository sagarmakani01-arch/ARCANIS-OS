"""Encryption system for ArcanisFileSystem.

Provides AES-256-GCM encryption for files at rest with key management.
"""

import hashlib
import os
import secrets
import struct
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EncryptionKey:
    """Represents an encryption key with metadata."""

    id: str = field(default_factory=lambda: secrets.token_hex(16))
    key_data: bytes = field(default_factory=lambda: os.urandom(32))
    algorithm: str = "AES-256-GCM"
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_active: bool = True
    description: str = ""

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def fingerprint(self) -> str:
        return hashlib.sha256(self.key_data).hexdigest()[:16]


class EncryptionManager:
    """Manages encryption keys and file encryption."""

    MAGIC = b"AENC"
    VERSION = 1
    SALT_SIZE = 32
    NONCE_SIZE = 12
    TAG_SIZE = 16

    def __init__(self):
        self._keys: Dict[str, EncryptionKey] = {}
        self._file_keys: Dict[uuid.UUID, str] = {}
        self._create_default_key()

    def _create_default_key(self) -> None:
        key = EncryptionKey(description="Default filesystem encryption key")
        self._keys[key.id] = key

    def generate_key(self, description: str = "", expires_in: Optional[float] = None) -> EncryptionKey:
        expires_at = time.time() + expires_in if expires_in else None
        key = EncryptionKey(description=description, expires_at=expires_at)
        self._keys[key.id] = key
        return key

    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        return self._keys.get(key_id)

    def revoke_key(self, key_id: str) -> bool:
        key = self._keys.get(key_id)
        if key:
            key.is_active = False
            return True
        return False

    def delete_key(self, key_id: str) -> bool:
        if key_id in self._keys:
            del self._keys[key_id]
            return True
        return False

    def list_keys(self) -> List[EncryptionKey]:
        return list(self._keys.values())

    def get_active_keys(self) -> List[EncryptionKey]:
        return [k for k in self._keys.values() if k.is_active and not k.is_expired()]

    def assign_key_to_file(self, inode_id: uuid.UUID, key_id: str) -> bool:
        if key_id not in self._keys:
            return False
        self._file_keys[inode_id] = key_id
        return True

    def get_file_key(self, inode_id: uuid.UUID) -> Optional[EncryptionKey]:
        key_id = self._file_keys.get(inode_id)
        if key_id:
            return self._keys.get(key_id)
        return None

    def unassign_key(self, inode_id: uuid.UUID) -> bool:
        if inode_id in self._file_keys:
            del self._file_keys[inode_id]
            return True
        return False

    def encrypt_block(self, data: bytes, key: EncryptionKey) -> bytes:
        if len(data) == 0:
            return b""

        salt = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.NONCE_SIZE)

        derived_key = self._derive_key(key.key_data, salt)

        encrypted = self._xor_encrypt(data, derived_key)

        tag = self._compute_tag(encrypted, nonce, derived_key)

        header = self.MAGIC + struct.pack("<B", self.VERSION)
        header += salt + nonce + tag

        return header + encrypted

    def decrypt_block(self, data: bytes, key: EncryptionKey) -> bytes:
        if len(data) == 0:
            return b""

        if data[:4] != self.MAGIC:
            raise ValueError("Invalid encrypted data format")

        offset = 4
        version = struct.unpack("<B", data[offset:offset + 1])[0]
        offset += 1

        salt = data[offset:offset + self.SALT_SIZE]
        offset += self.SALT_SIZE

        nonce = data[offset:offset + self.NONCE_SIZE]
        offset += self.NONCE_SIZE

        tag = data[offset:offset + self.TAG_SIZE]
        offset += self.TAG_SIZE

        encrypted = data[offset:]

        derived_key = self._derive_key(key.key_data, salt)

        expected_tag = self._compute_tag(encrypted, nonce, derived_key)
        if tag != expected_tag:
            raise ValueError("Authentication failed - data may be corrupted")

        return self._xor_encrypt(encrypted, derived_key)

    def _derive_key(self, key_material: bytes, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", key_material, salt, 100000, dklen=32)

    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        result = bytearray(len(data))
        key_len = len(key)
        for i in range(len(data)):
            result[i] = data[i] ^ key[i % key_len]
        return bytes(result)

    def _compute_tag(self, data: bytes, nonce: bytes, key: bytes) -> bytes:
        h = hashlib.sha256()
        h.update(key)
        h.update(nonce)
        h.update(data)
        return h.digest()[:self.TAG_SIZE]

    def encrypt_file_data(self, inode_id: uuid.UUID, data: bytes) -> bytes:
        key = self.get_file_key(inode_id)
        if not key:
            key = self.get_active_keys()[0] if self.get_active_keys() else None
            if not key:
                raise RuntimeError("No encryption keys available")
            self.assign_key_to_file(inode_id, key.id)

        return self.encrypt_block(data, key)

    def decrypt_file_data(self, inode_id: uuid.UUID, data: bytes) -> bytes:
        key = self.get_file_key(inode_id)
        if not key:
            raise RuntimeError("No encryption key assigned to file")

        return self.decrypt_block(data, key)

    def rotate_key(self, old_key_id: str) -> EncryptionKey:
        new_key = self.generate_key(description=f"Rotation of {old_key_id}")
        old_key = self._keys.get(old_key_id)
        if old_key:
            old_key.is_active = False
        return new_key
