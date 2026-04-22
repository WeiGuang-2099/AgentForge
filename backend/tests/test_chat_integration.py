"""Integration tests for chat with persistence."""
import pytest
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.message import Message
from app.routers.chat import _get_or_create_conversation, _save_message


@pytest.mark.asyncio
async def test_chat_creates_conversation_and_messages(db_session):
    """Chat endpoint creates conversation and persists messages."""
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
    result = await db_session.execute(
        select(Message).where(Message.conversation_id == conv.id)
    )
    messages = result.scalars().all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_get_or_create_returns_existing(db_session):
    """_get_or_create_conversation returns existing when ID matches."""
    conv1 = Conversation(agent_name="assistant", title="First")
    db_session.add(conv1)
    await db_session.commit()
    await db_session.refresh(conv1)

    conv2 = await _get_or_create_conversation(
        db_session, conversation_id=conv1.id, agent_name="assistant", first_message="Follow-up"
    )
    await db_session.commit()

    assert conv2.id == conv1.id
    assert conv2.title == "First"  # title not overwritten


@pytest.mark.asyncio
async def test_list_conversations_returns_created(db_session):
    """Listing conversations returns those created in database."""
    conv1 = Conversation(agent_name="assistant", title="Chat 1")
    conv2 = Conversation(agent_name="coder", title="Chat 2")
    db_session.add_all([conv1, conv2])
    await db_session.commit()

    result = await db_session.execute(select(Conversation))
    convs = result.scalars().all()
    assert len(convs) == 2


@pytest.mark.asyncio
async def test_delete_conversation_removes_messages(db_session):
    """Deleting a conversation also removes its messages."""
    conv = await _get_or_create_conversation(
        db_session, conversation_id=None, agent_name="assistant", first_message="Test"
    )
    await db_session.commit()

    await _save_message(db_session, conv.id, "user", "Test msg")
    await db_session.commit()

    # Delete conversation
    await db_session.delete(conv)
    await db_session.commit()

    result = await db_session.execute(select(Message))
    assert len(result.scalars().all()) == 0
