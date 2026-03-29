"""
工具包 - 自动注册所有内置工具。

在应用启动时调用 register_all_tools() 注册所有工具。
"""
from app.tools.base import tool_registry

def register_all_tools():
    """注册所有内置工具到全局注册表"""
    # 代码执行工具
    from app.tools.code import PythonReplTool
    tool_registry.register(PythonReplTool())
    
    # 搜索工具
    from app.tools.search import WebSearchTool, WebScrapeTool
    tool_registry.register(WebSearchTool())
    tool_registry.register(WebScrapeTool())
    
    # 文件操作与数据分析工具
    from app.tools.file import ReadFileTool, WriteFileTool
    from app.tools.data import CalculatorTool, DataAnalyzerTool, TranslatorTool
    
    tool_registry.register(ReadFileTool())
    tool_registry.register(WriteFileTool())
    tool_registry.register(CalculatorTool())
    tool_registry.register(DataAnalyzerTool())
    tool_registry.register(TranslatorTool())
