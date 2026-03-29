"""User model."""
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, CreatedAtMixin


class User(Base, UUIDMixin, CreatedAtMixin):
    """User model for storing user information."""
    
    __tablename__ = "users"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 可选，允许无密码用户
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"
