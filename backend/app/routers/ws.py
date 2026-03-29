"""WebSocket 实时通信路由"""
import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
        logger.info(f"WebSocket 已连接: {conversation_id}")
    
    def disconnect(self, conversation_id: str):
        self.active_connections.pop(conversation_id, None)
        logger.info(f"WebSocket 已断开: {conversation_id}")
    
    async def send_json(self, conversation_id: str, data: dict):
        ws = self.active_connections.get(conversation_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """
    WebSocket 对话端点
    
    客户端发送格式:
    {
        "type": "chat",
        "agent_name": "assistant",
        "messages": [{"role": "user", "content": "..."}]
    }
    
    服务端推送格式:
    - 流式token: {"type": "token", "content": "..."}
    - 完成: {"type": "done"}
    - 错误: {"type": "error", "message": "..."}
    - 心跳: {"type": "pong"}
    """
    from app.main import get_engine
    engine = get_engine()
    
    await manager.connect(conversation_id, websocket)
    
    try:
        while True:
            # 接收客户端消息
            raw_data = await websocket.receive_text()
            
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "无效的 JSON 格式"})
                continue
            
            msg_type = data.get("type", "")
            
            # 心跳
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            
            # 聊天消息
            if msg_type == "chat":
                agent_name = data.get("agent_name", "assistant")
                messages = data.get("messages", [])
                
                if not messages:
                    await websocket.send_json({"type": "error", "message": "消息列表不能为空"})
                    continue
                
                try:
                    # 流式返回
                    async for token in engine.run_stream(agent_name, messages):
                        await websocket.send_json({
                            "type": "token",
                            "content": token,
                        })
                    
                    # 完成标记
                    await websocket.send_json({"type": "done"})
                    
                except Exception as e:
                    logger.error(f"Agent 执行错误: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })
            else:
                await websocket.send_json({"type": "error", "message": f"未知消息类型: {msg_type}"})
    
    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
        manager.disconnect(conversation_id)
