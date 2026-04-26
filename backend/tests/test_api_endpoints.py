"""Tests for API endpoints."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event

from app.models.base import Base
from app.models.database import get_db
from app.main import app


# --- Fixtures for overriding DB ---

_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")


@event.listens_for(_test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# Apply the override
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
async def _setup_test_db():
    """Create tables before each test and drop after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# --- Health endpoint ---

async def test_health_endpoint():
    """GET /api/health returns 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# --- Agent endpoints ---

async def test_list_agents():
    """GET /api/agents returns 200 with list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# --- Tool endpoints ---

async def test_list_tools():
    """GET /api/tools returns 200 with list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/tools")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# --- Auth endpoints ---

async def test_register_and_login():
    """POST /api/auth/register then POST /api/auth/login returns tokens."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        reg_response = await client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "testuser_api@example.com",
            "password": "securepassword123"
        })
        assert reg_response.status_code == 200
        reg_data = reg_response.json()
        assert "access_token" in reg_data
        assert "refresh_token" in reg_data

        # Login
        login_response = await client.post("/api/auth/login", json={
            "email": "testuser_api@example.com",
            "password": "securepassword123"
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"


# --- Chat endpoints ---

async def test_chat_endpoint():
    """POST /api/chat with valid agent returns response (mock LLM)."""
    mock_response = MagicMock(
        content="Hello from mocked LLM",
        model="test-model",
        usage={"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        finish_reason="stop",
        raw_response=None,
    )

    with patch("app.core.agent.AgentEngine.run", new_callable=AsyncMock, return_value=mock_response):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/chat", json={
                "agent_name": "assistant",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            })
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello from mocked LLM"


async def test_chat_invalid_agent():
    """POST /api/chat with nonexistent agent returns 404."""
    from app.core.agent import AgentNotFoundError

    async def raise_not_found(*args, **kwargs):
        raise AgentNotFoundError("Agent 'nonexistent_agent_xyz' not found")

    with patch("app.core.agent.AgentEngine.run", side_effect=raise_not_found):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/chat", json={
                "agent_name": "nonexistent_agent_xyz",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            })
        assert response.status_code == 404
