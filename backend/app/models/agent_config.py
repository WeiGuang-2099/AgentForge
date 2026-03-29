"""AgentConfig model."""
from typing import Any, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin


class AgentConfig(Base, UUIDMixin, TimestampMixin):
    """AgentConfig model for storing agent configurations."""
    
    __tablename__ = "agent_configs"
    
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tools: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    memory: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    parameters: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        return f"<AgentConfig(id={self.id}, name={self.name}, is_preset={self.is_preset})>"
