# Phase 1: Data Persistence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire all API endpoints to the database so that conversations, usage stats, audit logs, and auth all persist and return real data.

**Architecture:** Use the existing SQLAlchemy async models (already defined in `backend/app/models/`). The main work is (a) adding Alembic migrations, (b) modifying routers to read/write through the DB session instead of returning hardcoded values, and (c) injecting audit/usage recording into the Agent execution path.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic, Pytest + pytest-asyncio

---

## Task 1: Set up Alembic for database migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/` (directory)
- Modify: `backend/pyproject.toml` (add alembic dependency)
- Modify: `requirements.txt` (add alembic dependency)

**Step 1: Add alembic dependency**

Add `alembic>=1.13.0` to `backend/pyproject.toml` under `dependencies` and to `requirements.txt`.

**Step 2: Initialize Alembic**

Run from `backend/` directory:
```bash
cd backend && alembic init alembic
```

**Step 3: Configure alembic/env.py**

Replace `backend/alembic/env.py` to use async engine from our config:

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.config import settings
from app.models.base import Base

# Import all models so Base.metadata knows about them
from app.models import (  # noqa: F401
    User, Conversation, Message, AgentConfig,
    UserApiKey, AuditLog, UsageRecord,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 4: Configure alembic.ini**

Set `sqlalchemy.url` in `backend/alembic.ini` to a placeholder (it will be overridden by env.py):
```ini
sqlalchemy.url = postgresql+asyncpg://placeholder
```

**Step 5: Generate initial migration**

```bash
cd backend && alembic revision --autogenerate -m "initial tables"
```

Verify the generated migration includes all 7 tables: users, conversations, messages, agent_configs, user_api_keys, audit_logs, usage_records.

**Step 6: Test migration**

```bash
cd backend && alembic upgrade head
```

Ensure it runs without errors (requires a running PostgreSQL). Then downgrade and upgrade again:
```bash
cd backend && alembic downgrade base && alembic upgrade head
```

**Step 7: Commit**

```bash
git add backend/alembic.ini backend/alembic/ backend/pyproject.toml requirements.txt
git commit -m "feat: add Alembic database migration setup"
```

---

## Task 2: Wire conversation persistence into chat router

**Files:**
- Modify: `backend/app/routers/chat.py`
- Create: `backend/tests/test_chat_persistence.py`

**Step 1: Write failing tests for conversation persistence**

Create `backend/tests/test_chat_persistence.py`:

```python
"""Tests for conversation persistence."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.base import Base
from app.models.conversation import Conversation
from app.models.message import Message


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_conversation_create(db_session):
    """Creating a conversation persists to database."""
    conv = Conversation(agent_name="assistant", title="Test Chat")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    result = await db_session.execute(select(Conversation))
    convs = result.scalars().all()
    assert len(convs) == 1
    assert convs[0].agent_name == "assistant"
    assert convs[0].title == "Test Chat"


@pytest.mark.asyncio
async def test_message_create(db_session):
    """Creating messages linked to a conversation persists correctly."""
    conv = Conversation(agent_name="assistant", title="Test")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    msg1 = Message(conversation_id=conv.id, role="user", content="Hello")
    msg2 = Message(conversation_id=conv.id, role="assistant", content="Hi there")
    db_session.add_all([msg1, msg2])
    await db_session.commit()

    result = await db_session.execute(
        select(Message).where(Message.conversation_id == conv.id)
    )
    messages = result.scalars().all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].content == "Hi there"


@pytest.mark.asyncio
async def test_conversation_cascade_delete(db_session):
    """Deleting a conversation cascades to delete its messages."""
    conv = Conversation(agent_name="assistant", title="Test")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    msg = Message(conversation_id=conv.id, role="user", content="Hello")
    db_session.add(msg)
    await db_session.commit()

    await db_session.delete(conv)
    await db_session.commit()

    result = await db_session.execute(select(Message))
    assert len(result.scalars().all()) == 0
```

**Step 2: Install test dependency and run tests to verify they fail**

```bash
cd backend && pip install aiosqlite && pytest tests/test_chat_persistence.py -v
```

Note: SQLite doesn't support PostgreSQL UUID natively. The models use `PG_UUID`. For tests to pass on SQLite, we need a small compatibility fix in the next step. If tests fail with import errors, that's expected at this stage.

**Step 3: Add SQLite test compatibility**

Create `backend/tests/conftest.py`:

```python
"""Shared test fixtures."""
import pytest
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
```

The models use `PG_UUID` which won't work on SQLite. Update `backend/app/models/base.py` to use a portable UUID type:

Replace the UUID import and UUIDMixin:
```python
"""SQLAlchemy 2.0 base classes and mixins."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class UUIDMixin:
    """Mixin that provides UUID primary key (stored as String for portability)."""
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
```

Then update all models that import `PG_UUID` to use `String(36)` instead. Files to update:
- `backend/app/models/conversation.py`: Change `from sqlalchemy.dialects.postgresql import UUID` to just use `String(36)` for foreign keys
- `backend/app/models/message.py`: Same change
- `backend/app/models/usage.py`: Change `PG_UUID` to `String(36)`
- `backend/app/models/audit_log.py`: Change `PG_UUID` to `String(36)`
- `backend/app/models/api_key.py`: Change `PG_UUID` to `String(36)`

For each model, replace:
```python
# Before
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
# ...
some_field: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ...)

# After
# Remove PG_UUID import
some_field: Mapped[str] = mapped_column(String(36), ...)
```

And for `UsageRecord` specifically, change UUID-typed columns to String(36) and remove `import uuid` / `uuid.uuid4` defaults in favor of `str(uuid4())`:

```python
id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
user_id: Mapped[str] = mapped_column(String(36), nullable=True)
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && pytest tests/test_chat_persistence.py -v
```

Expected: All 3 tests PASS.

**Step 5: Modify chat router to persist conversations and messages**

Replace `backend/app/routers/chat.py` with persistence logic:

```python
"""Conversation persistence + chat routes."""
import json
import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter()


# --- Pydantic Schemas ---

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    agent_name: str
    messages: list[ChatMessage]
    conversation_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    conversation_id: str
    agent_name: str
    content: str
    model: str
    usage: dict

class ConversationInfo(BaseModel):
    id: str
    agent_name: str
    title: str
    created_at: str
    updated_at: str

class MessageInfo(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


# --- Helpers ---

async def _get_or_create_conversation(
    db: AsyncSession,
    conversation_id: Optional[str],
    agent_name: str,
    first_message: str,
) -> Conversation:
    """Get existing conversation or create a new one."""
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

    # Create new conversation with title from first message
    title = first_message[:50] + ("..." if len(first_message) > 50 else "")
    conv = Conversation(agent_name=agent_name, title=title)
    db.add(conv)
    await db.flush()
    return conv


async def _save_message(
    db: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
) -> Message:
    """Persist a single message."""
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)
    await db.flush()
    return msg


# --- Routes ---

@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send message (non-streaming) with persistence."""
    from app.main import get_engine
    from app.core.agent import AgentNotFoundError
    from app.core.llm import LLMError
    engine = get_engine()

    try:
        # Get or create conversation
        first_msg = req.messages[0].content if req.messages else ""
        conv = await _get_or_create_conversation(
            db, req.conversation_id, req.agent_name, first_msg
        )

        # Save user messages
        for m in req.messages:
            await _save_message(db, conv.id, m.role, m.content)

        # Call LLM
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        response = await engine.run(req.agent_name, messages)

        # Save assistant response
        await _save_message(db, conv.id, "assistant", response.content)

        return ChatResponse(
            conversation_id=conv.id,
            agent_name=req.agent_name,
            content=response.content,
            model=response.model,
            usage=response.usage,
        )
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send message (streaming SSE) with persistence."""
    from app.main import get_engine
    from app.core.agent import AgentNotFoundError
    engine = get_engine()

    profile = engine.get_agent(req.agent_name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_name}' not found")

    first_msg = req.messages[0].content if req.messages else ""
    conv = await _get_or_create_conversation(
        db, req.conversation_id, req.agent_name, first_msg
    )

    # Save user messages
    for m in req.messages:
        await _save_message(db, conv.id, m.role, m.content)

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    async def event_generator():
        full_content = []
        try:
            async for token in engine.run_stream(req.agent_name, messages):
                full_content.append(token)
                data = json.dumps({"token": token, "conversation_id": conv.id}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # Save complete assistant response
            # Need a new db session since this runs in a different context
            from app.models.database import AsyncSessionLocal
            async with AsyncSessionLocal() as save_session:
                msg = Message(conversation_id=conv.id, role="assistant", content="".join(full_content))
                save_session.add(msg)
                await save_session.commit()

            yield f"data: {json.dumps({'done': True, 'conversation_id': conv.id})}\n\n"
        except Exception as e:
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=list[ConversationInfo])
async def list_conversations(
    agent_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List conversations from database."""
    query = select(Conversation).order_by(desc(Conversation.updated_at))
    if agent_name:
        query = query.where(Conversation.agent_name == agent_name)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    convs = result.scalars().all()
    return [
        ConversationInfo(
            id=str(c.id),
            agent_name=c.agent_name,
            title=c.title,
            created_at=c.created_at.isoformat() if c.created_at else "",
            updated_at=c.updated_at.isoformat() if c.updated_at else "",
        )
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageInfo])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get messages for a conversation from database."""
    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        MessageInfo(
            id=str(m.id),
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat() if m.created_at else "",
        )
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    return {"message": "Conversation deleted"}
```

**Step 6: Commit**

```bash
git add backend/app/routers/chat.py backend/app/models/base.py backend/app/models/conversation.py backend/app/models/message.py backend/app/models/usage.py backend/app/models/audit_log.py backend/app/models/api_key.py backend/tests/test_chat_persistence.py backend/tests/conftest.py
git commit -m "feat: wire conversation persistence into chat router, portable UUID types"
```

---

## Task 3: Add usage statistics recording after LLM calls

**Files:**
- Modify: `backend/app/core/agent.py` (inject usage recording into run/run_stream)
- Create: `backend/app/utils/usage.py`
- Create: `backend/tests/test_usage_recording.py`

**Step 1: Create usage recording utility**

Create `backend/app/utils/usage.py`:

```python
"""Usage statistics recording utility."""
import logging
from typing import Optional

from app.models.usage import UsageRecord

logger = logging.getLogger(__name__)


async def record_usage(
    db_session,
    agent_name: str,
    model: str,
    usage: dict,
    user_id: Optional[str] = None,
) -> None:
    """
    Record a single LLM usage entry.

    Silently logs errors to avoid disrupting the chat flow.
    """
    try:
        record = UsageRecord(
            user_id=user_id,
            agent_name=agent_name,
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
        db_session.add(record)
        await db_session.commit()
    except Exception as e:
        logger.error(f"Failed to record usage: {e}")
```

**Step 2: Write failing test**

Create `backend/tests/test_usage_recording.py`:

```python
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
    # Pass a session with invalid state
    await record_usage(
        None,  # type: ignore
        agent_name="assistant",
        model="gpt-4",
        usage={},
    )
    # Should not raise
```

**Step 3: Run tests**

```bash
cd backend && pytest tests/test_usage_recording.py -v
```

Expected: First test PASSES, second test PASSES (error is caught).

**Step 4: Modify chat router to record usage after LLM calls**

In `backend/app/routers/chat.py`, after the response from `engine.run()`, add usage recording. Add at the top:

```python
from app.utils.usage import record_usage
```

Then in the `chat()` endpoint, after `response = await engine.run(...)`, add:

```python
        # Record usage
        await record_usage(
            db,
            agent_name=req.agent_name,
            model=response.model,
            usage=response.usage,
        )
```

Note: The streaming endpoint will need a similar approach but using a separate session in the generator.

**Step 5: Commit**

```bash
git add backend/app/utils/usage.py backend/app/routers/chat.py backend/tests/test_usage_recording.py
git commit -m "feat: record usage statistics after LLM calls"
```

---

## Task 4: Wire audit log recording into sensitive endpoints

**Files:**
- Modify: `backend/app/routers/auth.py` (record login/register/logout)
- Modify: `backend/app/routers/apikey.py` (record key create/delete)
- Modify: `backend/app/routers/agent.py` (record agent create)
- Create: `backend/tests/test_audit_logging.py`

**Step 1: Write failing test**

Create `backend/tests/test_audit_logging.py`:

```python
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
    # Should not raise
```

**Step 2: Run tests**

```bash
cd backend && pytest tests/test_audit_logging.py -v
```

Expected: Both tests PASS (log_audit already exists and handles errors).

**Step 3: Add audit logging to auth router**

In `backend/app/routers/auth.py`, add after each operation:

After user registration (after `await db.refresh(user)`):
```python
    from app.utils.audit import log_audit
    await log_audit(db, action="register", user_id=str(user.id), resource_type="user", detail=f"User {user.name} registered")
```

After successful login (after token creation):
```python
    from app.utils.audit import log_audit
    await log_audit(db, action="login", user_id=str(user.id), resource_type="auth", detail=f"User {user.email} logged in")
```

**Step 4: Add audit logging to apikey router**

In `backend/app/routers/apikey.py`:

After saving a key:
```python
    from app.utils.audit import log_audit
    await log_audit(db, action="save_api_key", user_id=user_id, resource_type="api_key", detail=f"Saved {req.provider} key")
```

After deleting a key:
```python
    from app.utils.audit import log_audit
    await log_audit(db, action="delete_api_key", user_id=user_id, resource_type="api_key", detail=f"Deleted key {key_id}")
```

**Step 5: Add audit logging to agent router**

In `backend/app/routers/agent.py`, after creating an agent:
```python
    from app.utils.audit import log_audit
    # No db session in agent router currently - add Depends(get_db)
```

The agent router needs `db: AsyncSession = Depends(get_db)` added as a parameter, and the `log_audit` call after `create_agent`.

**Step 6: Commit**

```bash
git add backend/app/routers/auth.py backend/app/routers/apikey.py backend/app/routers/agent.py backend/tests/test_audit_logging.py
git commit -m "feat: add audit logging to auth, apikey, and agent endpoints"
```

---

## Task 5: Initialize database on startup and add init_db CLI

**Files:**
- Modify: `backend/app/main.py` (call init_db in lifespan)
- Modify: `backend/app/cli.py` (add init-db command)

**Step 1: Update main.py lifespan to initialize database**

In `backend/app/main.py`, add database initialization to the lifespan:

```python
from app.models.database import init_db, close_db
```

In the `lifespan` function, before `yield`:
```python
    # Initialize database tables
    await init_db()
    logger.info("Database initialized")
```

After `yield` (in the cleanup section):
```python
    await close_db()
```

**Step 2: Update CLI to support init-db command**

Read the current `backend/app/cli.py` and add an `init-db` subcommand that runs Alembic migrations.

**Step 3: Test startup manually**

```bash
cd backend && python -m app.main
```

Check that the log shows "Database initialized" and tables are created.

**Step 4: Commit**

```bash
git add backend/app/main.py backend/app/cli.py
git commit -m "feat: initialize database on app startup, add init-db CLI command"
```

---

## Task 6: Fix double-commit issue in get_db dependency

**Files:**
- Modify: `backend/app/models/database.py`

**Step 1: Fix get_db to not auto-commit**

The current `get_db()` commits after yield. But some routers (like `apikey.py`) commit explicitly. This causes double-commit issues.

Change `get_db` to NOT auto-commit -- let routers control their own commits:

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

**Step 2: Ensure all routers that use get_db commit explicitly**

Verify these routers have explicit `await db.commit()` calls:
- `auth.py` -- already has commits
- `apikey.py` -- already has commits
- `chat.py` -- the new version needs explicit commits
- `usage.py` -- read-only, no commits needed
- `audit.py` -- read-only, no commits needed

For `chat.py`, add `await db.commit()` after saving conversation and messages in the non-streaming endpoint.

**Step 3: Commit**

```bash
git add backend/app/models/database.py backend/app/routers/chat.py
git commit -m "fix: remove auto-commit from get_db, routers control their own transactions"
```

---

## Task 7: Add integration test for the full chat flow

**Files:**
- Create: `backend/tests/test_chat_integration.py`

**Step 1: Write integration test**

Create `backend/tests/test_chat_integration.py`:

```python
"""Integration tests for chat with persistence."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    response = MagicMock()
    response.content = "Hello! How can I help you?"
    response.model = "gpt-4-turbo-preview"
    response.usage = {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
    return response


@pytest.mark.asyncio
async def test_chat_creates_conversation_and_messages(db_session):
    """Chat endpoint creates conversation and persists messages."""
    # This test verifies the data flow without starting the full server.
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.routers.chat import _get_or_create_conversation, _save_message

    # Create conversation
    conv = await _get_or_create_conversation(
        db_session, conversation_id=None, agent_name="assistant", first_message="Hi"
    )
    await db_session.commit()

    assert conv.id is not None
    assert conv.agent_name == "assistant"
    assert conv.title == "Hi"

    # Save messages
    await _save_message(db_session, conv.id, "user", "Hi")
    await _save_message(db_session, conv.id, "assistant", "Hello!")
    await db_session.commit()

    # Verify
    from sqlalchemy import select
    result = await db_session.execute(
        select(Message).where(Message.conversation_id == conv.id)
    )
    messages = result.scalars().all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_list_conversations_returns_created(db_session):
    """list_conversations returns conversations from database."""
    from app.models.conversation import Conversation

    conv1 = Conversation(agent_name="assistant", title="Chat 1")
    conv2 = Conversation(agent_name="coder", title="Chat 2")
    db_session.add_all([conv1, conv2])
    await db_session.commit()

    from sqlalchemy import select
    result = await db_session.execute(select(Conversation))
    convs = result.scalars().all()
    assert len(convs) == 2
```

**Step 2: Run all tests**

```bash
cd backend && pytest tests/ -v
```

Expected: All tests PASS.

**Step 3: Commit**

```bash
git add backend/tests/test_chat_integration.py
git commit -m "test: add integration tests for chat persistence flow"
```

---

## Task 8: Update frontend API client for new endpoints

**Files:**
- Modify: `frontend/src/lib/api.ts` (add conversation CRUD calls)

**Step 1: Read current frontend API client**

Read `frontend/src/lib/api.ts` to understand existing API calls.

**Step 2: Add conversation management functions**

Add to `frontend/src/lib/api.ts`:

```typescript
// Conversation management
export async function listConversations(agentName?: string) {
  const params = new URLSearchParams();
  if (agentName) params.set("agent_name", agentName);
  const resp = await fetch(`/api/conversations?${params}`);
  if (!resp.ok) throw new Error("Failed to fetch conversations");
  return resp.json();
}

export async function getConversationMessages(conversationId: string) {
  const resp = await fetch(`/api/conversations/${conversationId}/messages`);
  if (!resp.ok) throw new Error("Failed to fetch messages");
  return resp.json();
}

export async function deleteConversation(conversationId: string) {
  const resp = await fetch(`/api/conversations/${conversationId}`, { method: "DELETE" });
  if (!resp.ok) throw new Error("Failed to delete conversation");
  return resp.json();
}
```

**Step 3: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: add conversation CRUD API calls to frontend client"
```

---

## Summary

After completing all 8 tasks:

| What | Status |
|------|--------|
| Alembic migrations | Working, 7 tables |
| Conversation persistence | Chat saves/loads from DB |
| Message persistence | Messages linked to conversations |
| Usage statistics | Recorded after every LLM call |
| Audit logging | Auth, API key, agent actions logged |
| Database init on startup | Tables auto-created |
| Double-commit fix | Routers control their own transactions |
| Tests | Unit + integration tests passing |
| Frontend API client | Conversation CRUD calls added |

**Next phase:** Phase 2 - Memory System (short-term + long-term ChromaDB)
