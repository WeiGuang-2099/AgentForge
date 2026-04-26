"""Add database indexes for performance

Revision ID: 002
Revises: 001_initial
Create Date: 2026-04-26
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Messages table - frequent lookup by conversation
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    # Conversations table - frequent filtering
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_index("ix_conversations_agent_name", "conversations", ["agent_name"])

    # Audit logs - frequent time-range and user queries
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])

    # Usage records - frequent aggregation queries
    op.create_index("ix_usage_records_agent_name", "usage_records", ["agent_name"])
    op.create_index("ix_usage_records_created_at", "usage_records", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_usage_records_created_at", "usage_records")
    op.drop_index("ix_usage_records_agent_name", "usage_records")
    op.drop_index("ix_audit_logs_user_id", "audit_logs")
    op.drop_index("ix_audit_logs_created_at", "audit_logs")
    op.drop_index("ix_conversations_agent_name", "conversations")
    op.drop_index("ix_conversations_user_id", "conversations")
    op.drop_index("ix_messages_conversation_id", "messages")
