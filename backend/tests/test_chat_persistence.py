"""Tests for conversation persistence."""
import pytest
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.message import Message


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
