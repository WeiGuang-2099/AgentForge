"""工具执行器 - 解析 LLM tool_calls 并执行对应工具"""
import json
import asyncio
import logging
from typing import Optional

from app.tools.base import ToolRegistry, ToolResult, tool_registry
from app.config import settings

logger = logging.getLogger(__name__)

# 工具执行超时（秒）
DEFAULT_TIMEOUT = 30

# Mapping of tools to their feature flags
TOOL_FEATURE_FLAGS = {
    "python_repl": "ENABLE_CODE_EXECUTION",
    "web_search": "ENABLE_WEB_SEARCH",
    "web_scrape": "ENABLE_WEB_SEARCH",
    "read_file": "ENABLE_FILE_OPS",
    "write_file": "ENABLE_FILE_OPS",
}


class ToolRunner:
    """
    工具执行器。
    
    负责解析 LLM 返回的 tool_calls，调用对应工具，
    并将结果格式化为可回传给 LLM 的消息。
    """
    
    def __init__(self, registry: Optional[ToolRegistry] = None, timeout: int = DEFAULT_TIMEOUT):
        self.registry = registry or tool_registry
        self.timeout = timeout
    
    async def execute_tool_call(self, tool_name: str, arguments: dict) -> ToolResult:
        """
        执行单次工具调用。
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数（已解析的 dict）
            
        Returns:
            ToolResult
        """
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{tool_name}' not found",
            )
        
        # Check feature flag
        flag_name = TOOL_FEATURE_FLAGS.get(tool_name)
        if flag_name and not getattr(settings, flag_name, True):
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{tool_name}' is disabled by configuration",
            )
        
        try:
            result = await asyncio.wait_for(
                tool.execute(**arguments),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{tool_name}' execution timed out ({self.timeout}s)",
            )
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution error: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Tool execution error: {str(e)}",
            )
    
    async def process_tool_calls(self, tool_calls: list) -> list[dict]:
        """
        处理 LLM 返回的多个 tool_calls。
        
        Args:
            tool_calls: LLM 返回的 tool_calls 列表
            （每个元素包含 id, function.name, function.arguments）
            
        Returns:
            list[dict]: tool 角色的消息列表，可直接追加到对话中
        """
        tool_messages = []
        
        for tool_call in tool_calls:
            func = tool_call.function
            tool_name = func.name
            
            # 解析参数
            try:
                arguments = json.loads(func.arguments) if isinstance(func.arguments, str) else func.arguments
            except json.JSONDecodeError:
                arguments = {}
            
            logger.info(f"Executing tool: {tool_name}, args: {arguments}")
            
            # 执行工具
            result = await self.execute_tool_call(tool_name, arguments)
            
            # 构建 tool 消息
            content = result.output if result.success else f"Error: {result.error}"
            tool_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": content,
            })
            
            logger.info(f"Tool '{tool_name}' executed {'successfully' if result.success else 'failed'}")
        
        return tool_messages
