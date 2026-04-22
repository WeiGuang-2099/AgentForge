"""用户 API Key 加密存储模型"""
from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin


class UserApiKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_api_keys"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_hint: Mapped[str] = mapped_column(String(20), default="")
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
