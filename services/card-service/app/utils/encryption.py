import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings


def _derive_fernet_key() -> bytes:
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_derive_fernet_key())


def encrypt_field(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()
