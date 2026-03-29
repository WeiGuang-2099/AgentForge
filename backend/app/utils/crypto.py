"""AES-256 加密/解密工具"""
import base64
import hashlib
from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    """使用 APP_SECRET_KEY 派生 Fernet 密钥"""
    key = hashlib.sha256(settings.APP_SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt(plain_text: str) -> str:
    """加密"""
    f = _get_fernet()
    return f.encrypt(plain_text.encode()).decode()


def decrypt(encrypted_text: str) -> str:
    """解密"""
    f = _get_fernet()
    return f.decrypt(encrypted_text.encode()).decode()


def get_key_hint(api_key: str) -> str:
    """生成 key 显示提示（如 sk-...xxxx）"""
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}...{api_key[-4:]}"
