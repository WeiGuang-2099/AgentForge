"""工具基类和注册系统"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str  # string, integer, number, boolean, array, object
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[list] = None


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseTool(ABC):
    """
    工具抽象基类。
    
    所有工具必须继承此类并实现 execute 方法。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一标识名"""
        ...
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（会发送给 LLM）"""
        ...
    
    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """工具参数列表"""
        ...
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具。
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        ...
    
    def to_openai_function(self) -> dict:
        """
        将工具转换为 OpenAI function calling 格式。
        
        Returns:
            dict: OpenAI tool 定义
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str) -> None:
        """注销工具"""
        self._tools.pop(name, None)
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_all(self) -> list[BaseTool]:
        """列出所有工具"""
        return list(self._tools.values())
    
    def get_tools_by_names(self, names: list[str]) -> list[BaseTool]:
        """按名称列表获取工具"""
        return [self._tools[n] for n in names if n in self._tools]
    
    def get_openai_tools(self, names: Optional[list[str]] = None) -> list[dict]:
        """获取 OpenAI function calling 格式的工具定义列表"""
        tools = self.get_tools_by_names(names) if names else self.list_all()
        return [t.to_openai_function() for t in tools]


# 全局注册表实例
tool_registry = ToolRegistry()
