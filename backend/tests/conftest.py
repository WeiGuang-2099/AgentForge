"""Shared test fixtures."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event

from app.models.base import Base


@pytest.fixture
async def db_session():
    """In-memory SQLite async session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # Enable foreign key support in SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def mock_llm_client():
    """Mock LLM client that returns predictable responses."""
    client = AsyncMock()
    client.acomplete = AsyncMock(return_value=MagicMock(
        content="Test response from LLM",
        model="test-model",
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        finish_reason="stop",
        raw_response=None
    ))
    client.astream = AsyncMock()
    client.acomplete_with_tools = AsyncMock(return_value=MagicMock(
        content="Test response",
        model="test-model",
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        finish_reason="stop",
        raw_response=MagicMock(choices=[MagicMock(message=MagicMock(tool_calls=None))])
    ))
    return client


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing."""
    return {
        "name": "test_agent",
        "display_name": "Test Agent",
        "description": "A test agent",
        "model": "gpt-4",
        "system_prompt": "You are a test assistant.",
        "tools": [],
        "parameters": {"temperature": 0.7, "max_tokens": 1000},
    }


@pytest.fixture
def test_client():
    """FastAPI test client."""
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
