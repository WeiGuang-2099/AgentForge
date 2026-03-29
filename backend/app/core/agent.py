"""
Agent 核心引擎 - 管理 Agent 生命周期和对话执行。
"""
import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

import yaml

from app.core.llm import LLMClient, LLMResponse, LLMError
from app.core.tool_runner import ToolRunner
from app.tools.base import tool_registry

logger = logging.getLogger(__name__)


@dataclass
class AgentProfile:
    """Agent 配置的内存表示"""
    name: str
    display_name: str
    description: str
    model: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    memory: Optional[dict] = None
    parameters: dict = field(default_factory=lambda: {"temperature": 0.7, "max_tokens": 2000})
    is_preset: bool = False


class AgentNotFoundError(Exception):
    """Agent 未找到异常"""
    pass


class AgentRegistry:
    """管理所有可用 Agent 的注册和发现"""
    
    def __init__(self):
        self._agents: dict[str, AgentProfile] = {}
    
    def register(self, profile: AgentProfile) -> None:
        """注册一个 Agent"""
        if profile.name in self._agents:
            logger.warning(f"Agent '{profile.name}' 已存在，将被覆盖")
        self._agents[profile.name] = profile
        logger.debug(f"已注册 Agent: {profile.name}")
    
    def unregister(self, name: str) -> None:
        """注销一个 Agent"""
        if name in self._agents:
            del self._agents[name]
            logger.debug(f"已注销 Agent: {name}")
        else:
            logger.warning(f"尝试注销不存在的 Agent: {name}")
    
    def get(self, name: str) -> Optional[AgentProfile]:
        """获取 Agent 配置"""
        return self._agents.get(name)
    
    def list_all(self) -> list[AgentProfile]:
        """列出所有已注册的 Agent"""
        return list(self._agents.values())
    
    def load_presets(self, presets_dir: str) -> int:
        """
        从 presets/ 目录加载所有 YAML 预设文件，返回加载数量。
        
        跳过 team/ 子目录（team 模式后续实现），
        仅加载单 Agent 模式的 yaml 文件。
        
        Args:
            presets_dir: presets 目录路径
            
        Returns:
            成功加载的 Agent 数量
        """
        presets_dir = os.path.normpath(presets_dir)
        if not os.path.isdir(presets_dir):
            logger.warning(f"Presets 目录不存在: {presets_dir}")
            return 0
        
        loaded_count = 0
        
        for filename in os.listdir(presets_dir):
            filepath = os.path.join(presets_dir, filename)
            
            # 跳过 team/ 子目录
            if os.path.isdir(filepath):
                logger.debug(f"跳过目录: {filename}")
                continue
            
            # 只处理 .yaml 和 .yml 文件
            if not filename.endswith(('.yaml', '.yml')):
                continue
            
            try:
                profile = self._load_yaml_preset(filepath)
                if profile:
                    self.register(profile)
                    loaded_count += 1
            except Exception as e:
                logger.error(f"加载预设文件失败 {filepath}: {e}")
        
        return loaded_count
    
    def _load_yaml_preset(self, filepath: str) -> Optional[AgentProfile]:
        """
        从 YAML 文件加载 AgentProfile。
        
        Args:
            filepath: YAML 文件路径
            
        Returns:
            AgentProfile 或 None（如果文件为空或格式不正确）
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            logger.debug(f"跳过空的预设文件: {filepath}")
            return None
        
        # 确保必需字段存在
        name = data.get('name')
        if not name:
            # 如果没有 name，使用文件名（去掉扩展名）
            name = os.path.splitext(os.path.basename(filepath))[0]
        
        return AgentProfile(
            name=name,
            display_name=data.get('display_name', name),
            description=data.get('description', ''),
            model=data.get('model', 'gpt-3.5-turbo'),
            system_prompt=data.get('system_prompt', ''),
            tools=data.get('tools', []),
            memory=data.get('memory'),
            parameters=data.get('parameters', {"temperature": 0.7, "max_tokens": 2000}),
            is_preset=True,
        )


class AgentEngine:
    """
    Agent 核心引擎 - 管理 Agent 生命周期和对话执行。
    """
    
    def __init__(self):
        self.registry = AgentRegistry()
        self._llm_clients: dict[str, LLMClient] = {}  # 按模型缓存 LLM 客户端
        self.tool_runner = ToolRunner()  # 工具执行器
    
    async def initialize(self) -> None:
        """初始化引擎：加载预置 Agent"""
        # 从 agent.py 所在位置计算 presets 目录路径
        # backend/app/core/agent.py -> backend/../presets = presets
        current_dir = os.path.dirname(__file__)
        presets_dir = os.path.join(current_dir, "..", "..", "..", "presets")
        presets_dir = os.path.normpath(presets_dir)
        
        count = self.registry.load_presets(presets_dir)
        logger.info(f"已加载 {count} 个预置 Agent")
    
    def _get_llm_client(self, model: str, parameters: dict = None) -> LLMClient:
        """
        获取或创建 LLM 客户端（按模型缓存）。
        
        Args:
            model: 模型名称
            parameters: 参数（目前未使用，LLMClient 使用调用时传入的参数）
            
        Returns:
            LLMClient 实例
        """
        if model not in self._llm_clients:
            self._llm_clients[model] = LLMClient(model=model)
            logger.debug(f"创建新的 LLMClient: {model}")
        return self._llm_clients[model]
    
    def _build_messages(
        self, 
        profile: AgentProfile, 
        conversation_messages: list[dict]
    ) -> list[dict]:
        """
        构建发送给 LLM 的完整消息列表。
        
        将 system_prompt 作为第一条 system 消息，
        然后拼接对话历史 messages。
        
        Args:
            profile: Agent 配置
            conversation_messages: 对话消息列表
            
        Returns:
            完整的消息列表
        """
        messages: list[dict] = []
        
        # 添加 system prompt 作为第一条消息
        if profile.system_prompt:
            messages.append({
                "role": "system",
                "content": profile.system_prompt
            })
        
        # 追加用户对话消息
        messages.extend(conversation_messages)
        
        return messages
    
    def _get_agent_tools(self, profile: AgentProfile) -> list[dict]:
        """
        获取 Agent 可用的工具定义（OpenAI function calling 格式）。
        
        Args:
            profile: Agent 配置
            
        Returns:
            工具定义列表（空列表表示无可用工具）
        """
        if not profile.tools:
            return []
        return tool_registry.get_openai_tools(profile.tools)
    
    async def run(
        self, 
        agent_name: str, 
        messages: list[dict], 
        **kwargs
    ) -> LLMResponse:
        """
        执行单次非流式对话（带工具调用循环）。
        
        Args:
            agent_name: Agent 名称
            messages: 用户消息列表 [{"role": "user", "content": "..."}]
            **kwargs: 额外的 LLM 参数
            
        Returns:
            LLMResponse
            
        Raises:
            AgentNotFoundError: Agent 不存在
            LLMError: LLM 调用失败
        """
        profile = self.registry.get(agent_name)
        if not profile:
            raise AgentNotFoundError(f"Agent '{agent_name}' 未找到")
        
        llm_client = self._get_llm_client(profile.model, profile.parameters)
        full_messages = self._build_messages(profile, messages)
        
        # 合并 profile.parameters 和 kwargs，kwargs 优先
        call_params = {**profile.parameters, **kwargs}
        
        # 获取 Agent 可用的工具定义
        tools_def = self._get_agent_tools(profile)
        
        # 工具调用循环（最多 10 轮）
        max_iterations = 10
        response = None
        
        for _ in range(max_iterations):
            if tools_def:
                response = await llm_client.acomplete_with_tools(full_messages, tools_def, **call_params)
            else:
                response = await llm_client.acomplete(full_messages, **call_params)
            
            # 检查是否有 tool_calls
            raw = response.raw_response
            if raw and raw.choices[0].message.tool_calls:
                tool_calls = raw.choices[0].message.tool_calls
                
                # 将 assistant 的 tool_calls 消息加入对话
                full_messages.append(raw.choices[0].message.model_dump())
                
                # 执行工具并获取结果
                tool_messages = await self.tool_runner.process_tool_calls(tool_calls)
                full_messages.extend(tool_messages)
                
                # 继续循环，让 LLM 处理工具结果
                continue
            
            # 没有 tool_calls，返回最终响应
            return response
        
        # 超过最大轮次，返回最后一次响应
        return response
    
    async def run_stream(
        self, 
        agent_name: str, 
        messages: list[dict], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式执行对话，逐 token 返回。
        
        如果 Agent 配置了工具，使用非流式调用完成工具循环，
        然后模拟流式输出最终响应。
        
        Args:
            agent_name: Agent 名称
            messages: 用户消息列表
            **kwargs: 额外参数
            
        Yields:
            str: 每个 token 的文本
            
        Raises:
            AgentNotFoundError: Agent 不存在
            LLMError: LLM 调用失败
        """
        profile = self.registry.get(agent_name)
        if not profile:
            raise AgentNotFoundError(f"Agent '{agent_name}' 未找到")
        
        # 如果 Agent 有工具，使用非流式 + 模拟流式（因为工具调用需要完整响应）
        if profile.tools and self._get_agent_tools(profile):
            response = await self.run(agent_name, messages, **kwargs)
            # 模拟流式输出
            for char in response.content:
                yield char
                await asyncio.sleep(0.01)  # 模拟打字效果
            return
        
        # 无工具的 Agent，正常流式
        llm_client = self._get_llm_client(profile.model, profile.parameters)
        full_messages = self._build_messages(profile, messages)
        
        # 合并 profile.parameters 和 kwargs，kwargs 优先
        call_params = {**profile.parameters, **kwargs}
        
        async for token in llm_client.astream(full_messages, **call_params):
            yield token
    
    def get_agent(self, name: str) -> Optional[AgentProfile]:
        """
        获取 Agent 配置信息。
        
        Args:
            name: Agent 名称
            
        Returns:
            AgentProfile 或 None
        """
        return self.registry.get(name)
    
    def list_agents(self) -> list[AgentProfile]:
        """
        列出所有可用 Agent。
        
        Returns:
            AgentProfile 列表
        """
        return self.registry.list_all()
    
    async def create_agent(self, profile: AgentProfile) -> AgentProfile:
        """
        创建并注册一个新的自定义 Agent。
        
        Args:
            profile: Agent 配置
            
        Returns:
            注册后的 AgentProfile
        """
        self.registry.register(profile)
        logger.info(f"已创建自定义 Agent: {profile.name}")
        return profile
