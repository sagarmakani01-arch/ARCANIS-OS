import os
import base64
from typing import Optional, Tuple


try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class CryptoEngine:
    def __init__(self, key: Optional[str] = None):
        if not HAS_CRYPTO:
            raise ImportError(
                "cryptography is required for encryption. Install with: pip install cryptography"
            )
        if key:
            self.key = self._derive_key(key)
        else:
            self.key = self._generate_key()
        self._fernet = Fernet(self.key)

    def _derive_key(self, password: str) -> bytes:
        salt = b"arcanisd_salt_v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _generate_key(self) -> bytes:
        return Fernet.generate_key()

    def encrypt(self, data: str) -> str:
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        return self._fernet.decrypt(encrypted_data.encode()).decode()

    def encrypt_bytes(self, data: bytes) -> bytes:
        return self._fernet.encrypt(data)

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        return self._fernet.decrypt(encrypted_data)

    def get_key(self) -> str:
        return self.key.decode()

    @staticmethod
    def generate_key() -> str:
        if not HAS_CRYPTO:
            raise ImportError("cryptography is required")
        return Fernet.generate_key().decode()
