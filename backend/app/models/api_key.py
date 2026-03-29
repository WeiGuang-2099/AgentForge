"""用户 API Key 加密存储模型"""
from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from app.models.base import Base, UUIDMixin, TimestampMixin


class UserApiKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_api_keys"
    
    user_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # openai, anthropic, google
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)  # AES-256 加密后的 key
    key_hint: Mapped[str] = mapped_column(String(20), default="")  # 显示提示 (如 sk-...xxxx)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
