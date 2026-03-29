"""示例插件 - 展示如何创建 AgentForge 插件"""
from app.plugins.base import ToolPlugin, PluginMetadata
from app.tools.base import BaseTool, ToolParameter, ToolResult


class EchoTool(BaseTool):
    """回显工具 - 简单地返回输入内容"""
    
    @property
    def name(self) -> str:
        return "echo"
    
    @property
    def description(self) -> str:
        return "回显输入内容（示例工具）"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="text",
                type="string",
                description="要回显的文本"
            )
        ]
    
    async def execute(self, text: str = "", **kwargs) -> ToolResult:
        return ToolResult(success=True, output=f"Echo: {text}")


class Plugin(ToolPlugin):
    """示例插件 - 提供 echo 工具"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example",
            version="0.1.0",
            description="示例插件，提供 echo 工具",
            author="AgentForge",
        )
    
    def get_tools(self) -> list[BaseTool]:
        return [EchoTool()]
