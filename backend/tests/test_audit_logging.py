"""Tests for audit log recording."""
import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.utils.audit import log_audit


@pytest.mark.asyncio
async def test_log_audit_creates_entry(db_session):
    """log_audit creates an AuditLog entry."""
    await log_audit(
        db_session,
        action="login",
        user_id="test-user-id",
        resource_type="auth",
        detail="User logged in",
    )

    result = await db_session.execute(select(AuditLog))
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].action == "login"
    assert logs[0].user_id == "test-user-id"


@pytest.mark.asyncio
async def test_log_audit_handles_error(db_session):
    """log_audit does not raise on failure."""
    await log_audit(
        None,  # type: ignore
        action="test",
    )
