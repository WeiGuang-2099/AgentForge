"""插件基类定义"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str = ""
    homepage: str = ""
    dependencies: list[str] = field(default_factory=list)


class BasePlugin(ABC):
    """插件抽象基类"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """插件元数据"""
        ...
    
    @abstractmethod
    async def activate(self) -> None:
        """激活插件"""
        ...
    
    @abstractmethod
    async def deactivate(self) -> None:
        """停用插件"""
        ...


class ToolPlugin(BasePlugin):
    """
    工具插件 - 提供自定义工具。
    
    子类需要实现 get_tools() 返回 BaseTool 实例列表。
    """
    
    @abstractmethod
    def get_tools(self) -> list:
        """返回插件提供的工具列表（BaseTool 实例）"""
        ...
    
    async def activate(self) -> None:
        from app.tools.base import tool_registry
        for tool in self.get_tools():
            tool_registry.register(tool)
    
    async def deactivate(self) -> None:
        from app.tools.base import tool_registry
        for tool in self.get_tools():
            tool_registry.unregister(tool.name)


class AgentPlugin(BasePlugin):
    """
    Agent 插件 - 提供自定义 Agent 模板。
    
    子类需要实现 get_agents() 返回 AgentProfile 实例列表。
    """
    
    @abstractmethod
    def get_agents(self) -> list:
        """返回插件提供的 Agent 配置列表（AgentProfile 实例）"""
        ...
    
    async def activate(self) -> None:
        # 需要 AgentEngine 实例，通过 PluginManager 传入
        pass
    
    async def deactivate(self) -> None:
        pass
