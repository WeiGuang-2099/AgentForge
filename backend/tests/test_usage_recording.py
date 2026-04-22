"""Tests for usage recording."""
import pytest
from sqlalchemy import select

from app.models.usage import UsageRecord
from app.utils.usage import record_usage


@pytest.mark.asyncio
async def test_record_usage_creates_entry(db_session):
    """record_usage creates a UsageRecord in the database."""
    await record_usage(
        db_session,
        agent_name="assistant",
        model="gpt-4-turbo-preview",
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    )

    result = await db_session.execute(select(UsageRecord))
    records = result.scalars().all()
    assert len(records) == 1
    assert records[0].agent_name == "assistant"
    assert records[0].model == "gpt-4-turbo-preview"
    assert records[0].total_tokens == 150


@pytest.mark.asyncio
async def test_record_usage_handles_error(db_session):
    """record_usage does not raise on failure."""
    await record_usage(
        None,  # type: ignore
        agent_name="assistant",
        model="gpt-4",
        usage={},
    )
