"""审计日志模型"""
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
import uuid

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # chat, create_agent, login, etc.
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)  # agent, conversation, tool, etc.
    resource_id: Mapped[str] = mapped_column(String(100), nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
