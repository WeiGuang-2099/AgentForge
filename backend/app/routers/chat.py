"""对话路由"""
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

router = APIRouter()

# --- Pydantic Schemas ---

class ChatMessage(BaseModel):
    role: str  # user / assistant / system
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

# --- Routes ---

@router.post("/chat")
async def chat(req: ChatRequest):
    """发送消息（非流式）"""
    from app.main import get_engine
    from app.core.agent import AgentNotFoundError
    from app.core.llm import LLMError
    engine = get_engine()
    
    try:
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        response = await engine.run(req.agent_name, messages)
        
        conversation_id = req.conversation_id or str(uuid.uuid4())
        
        return ChatResponse(
            conversation_id=conversation_id,
            agent_name=req.agent_name,
            content=response.content,
            model=response.model,
            usage=response.usage,
        )
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {str(e)}")

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """发送消息（流式 SSE）"""
    from app.main import get_engine
    from app.core.agent import AgentNotFoundError
    engine = get_engine()
    
    profile = engine.get_agent(req.agent_name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_name}' 未找到")
    
    conversation_id = req.conversation_id or str(uuid.uuid4())
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    
    async def event_generator():
        try:
            async for token in engine.run_stream(req.agent_name, messages):
                data = json.dumps({"token": token, "conversation_id": conversation_id}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            # 发送结束标记
            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
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

@router.get("/conversations")
async def list_conversations():
    """获取会话列表（当前阶段返回空，后续接入数据库）"""
    return []

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """获取会话消息（当前阶段返回空，后续接入数据库）"""
    return []
