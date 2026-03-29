"""
LLM 客户端封装 - 基于 LiteLLM 的统一多模型调用接口
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional, Any
from dataclasses import dataclass, field

import litellm
from litellm import acompletion

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM 响应封装"""
    content: str
    model: str
    usage: dict = field(default_factory=dict)  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None


@dataclass  
class TokenUsage:
    """Token 使用量追踪"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMClient:
    """
    统一的 LLM 客户端，基于 LiteLLM 支持多提供商。
    
    支持的提供商：
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude 3 系列)
    - Google (Gemini Pro)
    - 智谱 AI (GLM-4 系列，使用 zhipuai/ 前缀)
    - 本地模型 (Ollama, LM Studio)
    """
    
    def __init__(
        self, 
        model: Optional[str] = None, 
        api_key: Optional[str] = None, 
        api_base: Optional[str] = None, 
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        初始化 LLM 客户端。
        
        Args:
            model: 模型名称，为 None 则从配置读取默认模型
            api_key: API Key，为 None 则从配置读取
            api_base: API Base URL（用于本地模型），为 None 则从配置读取
            max_retries: 最大重试次数
            timeout: 请求超时秒数
        """
        self.model = model or self._get_default_model()
        self.api_key = api_key
        self.api_base = api_base or settings.OPENAI_API_BASE
        self.max_retries = max_retries
        self.timeout = timeout
        self.total_usage = TokenUsage()
        
        # 配置 LiteLLM
        self._configure_litellm()
    
    def _get_default_model(self) -> str:
        """根据配置中可用的 API Key 选择默认模型"""
        if settings.OPENAI_API_KEY:
            return settings.OPENAI_MODEL
        elif settings.ANTHROPIC_API_KEY:
            return settings.ANTHROPIC_MODEL
        elif settings.OPENAI_API_BASE:
            return settings.OPENAI_MODEL
        return "gpt-3.5-turbo"  # 兜底默认
    
    def _configure_litellm(self) -> None:
        """配置 LiteLLM 全局设置"""
        litellm.drop_params = True  # 自动丢弃不支持的参数
        if settings.OPENAI_API_KEY:
            litellm.api_key = settings.OPENAI_API_KEY
        # 关闭 LiteLLM 自带日志减少噪音
        litellm.set_verbose = False
    
    def _build_kwargs(self, messages: list[dict], **kwargs) -> dict:
        """
        构建 LiteLLM 调用参数。
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Returns:
            构建好的调用参数字典
        """
        call_kwargs = {
            "model": kwargs.pop("model", self.model),
            "messages": messages,
            "timeout": kwargs.pop("timeout", self.timeout),
        }
        
        # API Key 处理：按模型前缀选择合适的 key
        model = call_kwargs["model"]
        if self.api_key:
            call_kwargs["api_key"] = self.api_key
        elif "claude" in model or "anthropic" in model:
            if settings.ANTHROPIC_API_KEY:
                call_kwargs["api_key"] = settings.ANTHROPIC_API_KEY
        elif "gemini" in model or "google" in model:
            if settings.GOOGLE_API_KEY:
                call_kwargs["api_key"] = settings.GOOGLE_API_KEY
        elif model.startswith("zhipuai/") or "glm" in model.lower():
            # 智谱 AI 模型（原生格式或 OpenAI 兼容模式）
            if settings.ZHIPUAI_API_KEY:
                call_kwargs["api_key"] = settings.ZHIPUAI_API_KEY
        else:
            if settings.OPENAI_API_KEY:
                call_kwargs["api_key"] = settings.OPENAI_API_KEY
        
        # API Base (本地模型)
        if self.api_base:
            call_kwargs["api_base"] = self.api_base
        
        # 可选参数透传
        optional_params = [
            "temperature", "max_tokens", "top_p", "stop", 
            "presence_penalty", "frequency_penalty", "tools",
            "tool_choice", "response_format"
        ]
        for param in optional_params:
            if param in kwargs:
                call_kwargs[param] = kwargs.pop(param)
        
        return call_kwargs
    
    async def acomplete(self, messages: list[dict], **kwargs) -> LLMResponse:
        """
        异步非流式调用。
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数（temperature, max_tokens 等）
        
        Returns:
            LLMResponse 对象
            
        Raises:
            LLMError: LLM 调用失败（重试耗尽后）
        """
        call_kwargs = self._build_kwargs(messages, **kwargs)
        
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await acompletion(**call_kwargs)
                
                # 提取响应内容
                choice = response.choices[0]
                usage_info: dict[str, int] = {}
                if hasattr(response, 'usage') and response.usage:
                    usage_info = {
                        "prompt_tokens": response.usage.prompt_tokens or 0,
                        "completion_tokens": response.usage.completion_tokens or 0,
                        "total_tokens": response.usage.total_tokens or 0,
                    }
                    # 累计用量
                    self.total_usage.prompt_tokens += usage_info["prompt_tokens"]
                    self.total_usage.completion_tokens += usage_info["completion_tokens"]
                    self.total_usage.total_tokens += usage_info["total_tokens"]
                
                return LLMResponse(
                    content=choice.message.content or "",
                    model=response.model or call_kwargs["model"],
                    usage=usage_info,
                    finish_reason=choice.finish_reason,
                    raw_response=response,
                )
            except Exception as e:
                last_error = e
                wait_time = (2 ** attempt) * 1  # 指数退避: 1s, 2s, 4s
                logger.warning(
                    f"LLM 调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}. "
                    f"等待 {wait_time}s 后重试..."
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
        
        raise LLMError(f"LLM 调用在 {self.max_retries} 次重试后仍然失败: {last_error}")
    
    async def astream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        """
        异步流式调用，逐 token 返回。
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Yields:
            str: 每个 token/chunk 的文本内容
            
        Raises:
            LLMError: LLM 流式调用失败（重试耗尽后）
        """
        call_kwargs = self._build_kwargs(messages, **kwargs)
        call_kwargs["stream"] = True
        
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await acompletion(**call_kwargs)
                
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            yield delta.content
                return  # 流正常结束
                
            except Exception as e:
                last_error = e
                wait_time = (2 ** attempt) * 1
                logger.warning(
                    f"LLM 流式调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}. "
                    f"等待 {wait_time}s 后重试..."
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
        
        raise LLMError(f"LLM 流式调用在 {self.max_retries} 次重试后仍然失败: {last_error}")
    
    async def acomplete_with_tools(
        self, 
        messages: list[dict], 
        tools: list[dict], 
        **kwargs
    ) -> LLMResponse:
        """
        带工具调用的异步完成。
        
        Args:
            messages: 消息列表
            tools: 工具定义列表 (OpenAI function calling 格式)
            **kwargs: 额外参数
            
        Returns:
            LLMResponse，raw_response 中包含 tool_calls 信息
        """
        kwargs["tools"] = tools
        kwargs["tool_choice"] = kwargs.get("tool_choice", "auto")
        return await self.acomplete(messages, **kwargs)
    
    def get_usage(self) -> dict[str, int]:
        """
        获取累计 token 使用量。
        
        Returns:
            包含 prompt_tokens, completion_tokens, total_tokens 的字典
        """
        return {
            "prompt_tokens": self.total_usage.prompt_tokens,
            "completion_tokens": self.total_usage.completion_tokens,
            "total_tokens": self.total_usage.total_tokens,
        }
    
    def reset_usage(self) -> None:
        """重置使用量计数"""
        self.total_usage = TokenUsage()


class LLMError(Exception):
    """LLM 调用异常"""
    pass
