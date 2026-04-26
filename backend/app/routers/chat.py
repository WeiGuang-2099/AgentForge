"""对话路由 - with persistence"""
import json
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.main import limiter
from app.models.database import get_db, AsyncSessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.utils.usage import record_usage
from app.core.auth import get_current_user_optional

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
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat(request: Request, req: ChatRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user_optional)):
    """Send message (non-streaming) with persistence."""
    from app.main import get_engine
    from app.core.agent import AgentNotFoundError
    from app.core.llm import LLMError
    engine = get_engine()

    try:
        first_msg = req.messages[0].content if req.messages else ""
        conv = await _get_or_create_conversation(
            db, req.conversation_id, req.agent_name, first_msg
        )

        for m in req.messages:
            await _save_message(db, conv.id, m.role, m.content)

        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        response = await engine.run(req.agent_name, messages)

        await _save_message(db, conv.id, "assistant", response.content)
        await db.commit()

        # Record usage
        await record_usage(
            db,
            agent_name=req.agent_name,
            model=response.model,
            usage=response.usage,
            user_id=current_user if current_user else None,
        )

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
        raise HTTPException(status_code=502, detail=f"LLM call failed: {str(e)}")


@router.post("/chat/stream")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat_stream(request: Request, req: ChatRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user_optional)):
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

    for m in req.messages:
        await _save_message(db, conv.id, m.role, m.content)
    await db.commit()

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    async def event_generator():
        full_content = []
        try:
            async for token in engine.run_stream(req.agent_name, messages):
                full_content.append(token)
                data = json.dumps({"token": token, "conversation_id": conv.id}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # Save complete assistant response using a separate session
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
    current_user = Depends(get_current_user_optional),
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
    current_user = Depends(get_current_user_optional),
):
    """Get messages for a conversation from database."""
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
    current_user = Depends(get_current_user_optional),
):
    """Delete a conversation and its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()
    return {"message": "Conversation deleted"}
