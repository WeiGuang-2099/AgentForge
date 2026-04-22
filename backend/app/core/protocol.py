"""
多 Agent 通信协议和编排器。

支持多个 Agent 之间的消息传递、任务分配和协同工作。
"""
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Agent 间消息类型"""
    TASK = "task"           # 任务分配
    RESULT = "result"       # 任务结果
    QUESTION = "question"   # 提问
    FEEDBACK = "feedback"   # 反馈
    STATUS = "status"       # 状态更新


class AgentStatus(str, Enum):
    """Agent 运行状态"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Agent 间消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""              # 发送者 Agent 名称
    receiver: str = ""            # 接收者 Agent 名称（空=广播）
    message_type: MessageType = MessageType.TASK
    content: str = ""
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentState:
    """Agent 运行时状态"""
    agent_name: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    messages: list[AgentMessage] = field(default_factory=list)


class MessageBus:
    """
    消息总线 - Agent 间通信的中间件。
    
    当前使用内存实现，后续可替换为 Redis 实现。
    """
    
    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._history: list[AgentMessage] = []
    
    def _ensure_queue(self, agent_name: str):
        if agent_name not in self._queues:
            self._queues[agent_name] = asyncio.Queue()
    
    async def send(self, message: AgentMessage) -> None:
        """发送消息到指定 Agent"""
        self._history.append(message)
        if message.receiver:
            self._ensure_queue(message.receiver)
            await self._queues[message.receiver].put(message)
        else:
            # 广播
            for name, queue in self._queues.items():
                if name != message.sender:
                    await queue.put(message)
    
    async def receive(self, agent_name: str, timeout: float = None) -> Optional[AgentMessage]:
        """接收消息"""
        self._ensure_queue(agent_name)
        try:
            if timeout:
                return await asyncio.wait_for(self._queues[agent_name].get(), timeout)
            return await self._queues[agent_name].get()
        except asyncio.TimeoutError:
            return None
    
    def get_history(self) -> list[AgentMessage]:
        """获取消息历史"""
        return self._history.copy()
    
    def clear(self):
        """清空消息"""
        self._queues.clear()
        self._history.clear()


class MultiAgentOrchestrator:
    """
    多 Agent 编排器。
    
    管理多个 Agent 的生命周期、消息路由和任务执行。
    """
    
    def __init__(self, engine: "AgentEngine"):
        """
        Args:
            engine: AgentEngine 实例，用于执行单个 Agent 的对话
        """
        self.engine = engine
        self.message_bus = MessageBus()
        self.agent_states: dict[str, AgentState] = {}
        self._running = False
    
    def _init_agent_state(self, agent_name: str) -> AgentState:
        """初始化 Agent 状态"""
        state = AgentState(agent_name=agent_name)
        self.agent_states[agent_name] = state
        return state
    
    def get_state(self, agent_name: str) -> Optional[AgentState]:
        """获取 Agent 状态"""
        return self.agent_states.get(agent_name)
    
    def get_all_states(self) -> dict[str, AgentState]:
        """获取所有 Agent 状态"""
        return self.agent_states.copy()
    
    async def assign_task(self, agent_name: str, task: str, context: dict = None) -> AgentMessage:
        """
        向指定 Agent 分配任务。
        
        Args:
            agent_name: 目标 Agent
            task: 任务描述
            context: 上下文信息（来自前置任务的结果等）
        
        Returns:
            AgentMessage: 发送的任务消息
        """
        message = AgentMessage(
            sender="orchestrator",
            receiver=agent_name,
            message_type=MessageType.TASK,
            content=task,
            metadata=context or {},
        )
        
        state = self.agent_states.get(agent_name) or self._init_agent_state(agent_name)
        state.status = AgentStatus.WORKING
        state.current_task = task
        
        await self.message_bus.send(message)
        return message
    
    async def execute_agent_task(self, agent_name: str, task: str, 
                                   context: dict = None) -> str:
        """
        执行单个 Agent 的任务。
        
        将任务和上下文组装成消息，调用 AgentEngine 执行，返回结果。
        
        Args:
            agent_name: Agent 名称
            task: 任务描述
            context: 上下文（前置任务结果）
            
        Returns:
            str: Agent 的响应内容
        """
        state = self.agent_states.get(agent_name) or self._init_agent_state(agent_name)
        state.status = AgentStatus.WORKING
        state.current_task = task
        
        # 构建消息：包含任务和上下文
        messages = []
        if context:
            context_str = "\n".join(f"[{k}]: {v}" for k, v in context.items())
            messages.append({
                "role": "user",
                "content": f"以下是之前团队成员的工作成果，供你参考：\n\n{context_str}",
            })
        messages.append({"role": "user", "content": task})
        
        try:
            response = await self.engine.run(agent_name, messages)
            state.status = AgentStatus.COMPLETED
            state.result = response.content
            
            # 记录结果消息
            result_msg = AgentMessage(
                sender=agent_name,
                receiver="orchestrator",
                message_type=MessageType.RESULT,
                content=response.content,
            )
            await self.message_bus.send(result_msg)
            
            return response.content
            
        except Exception as e:
            state.status = AgentStatus.ERROR
            state.error = str(e)
            logger.error(f"Agent '{agent_name}' execution failed: {e}")
            raise
    
    async def execute_agent_task_stream(self, agent_name: str, task: str,
                                          context: dict = None) -> AsyncGenerator[str, None]:
        """
        流式执行单个 Agent 的任务。
        
        Yields:
            str: 每个 token
        """
        state = self.agent_states.get(agent_name) or self._init_agent_state(agent_name)
        state.status = AgentStatus.WORKING
        state.current_task = task
        
        messages = []
        if context:
            context_str = "\n".join(f"[{k}]: {v}" for k, v in context.items())
            messages.append({
                "role": "user",
                "content": f"以下是之前团队成员的工作成果，供你参考：\n\n{context_str}",
            })
        messages.append({"role": "user", "content": task})
        
        full_content = ""
        try:
            async for token in self.engine.run_stream(agent_name, messages):
                full_content += token
                yield token
            
            state.status = AgentStatus.COMPLETED
            state.result = full_content
        except Exception as e:
            state.status = AgentStatus.ERROR
            state.error = str(e)
            raise
    
    def reset(self):
        """重置所有状态"""
        self.agent_states.clear()
        self.message_bus.clear()
