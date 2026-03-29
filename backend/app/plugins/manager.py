"""插件管理器 - 负责插件的发现、加载、激活和管理"""
import os
import importlib
import importlib.util
import logging
from dataclasses import dataclass
from typing import Optional

from app.plugins.base import BasePlugin, PluginMetadata, ToolPlugin, AgentPlugin

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """插件信息"""
    metadata: PluginMetadata
    plugin: BasePlugin
    is_active: bool = False


class PluginManager:
    """
    插件管理器。
    
    支持：
    - 从目录扫描和加载插件
    - 插件激活/停用
    - 插件状态管理
    """
    
    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = plugins_dir or os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "plugins"
        )
        self._plugins: dict[str, PluginInfo] = {}
    
    def discover_plugins(self) -> int:
        """
        扫描插件目录，发现可用插件。
        
        插件目录结构：
        plugins/
        ├── my_plugin/
        │   ├── __init__.py  (必须包含 Plugin 类)
        │   └── ...
        └── another_plugin/
            ├── __init__.py
            └── ...
        
        每个插件的 __init__.py 必须导出一个继承 BasePlugin 的 Plugin 类。
        
        Returns:
            int: 发现的插件数量
        """
        if not os.path.isdir(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            logger.info(f"已创建插件目录: {self.plugins_dir}")
            return 0
        
        count = 0
        for entry in os.listdir(self.plugins_dir):
            plugin_dir = os.path.join(self.plugins_dir, entry)
            init_file = os.path.join(plugin_dir, "__init__.py")
            
            if not os.path.isdir(plugin_dir) or not os.path.isfile(init_file):
                continue
            
            try:
                plugin = self._load_plugin(entry, init_file)
                if plugin:
                    info = PluginInfo(metadata=plugin.metadata, plugin=plugin)
                    self._plugins[plugin.metadata.name] = info
                    count += 1
                    logger.info(f"发现插件: {plugin.metadata.name} v{plugin.metadata.version}")
            except Exception as e:
                logger.warning(f"加载插件 '{entry}' 失败: {e}")
        
        return count
    
    def _load_plugin(self, module_name: str, init_file: str) -> Optional[BasePlugin]:
        """加载单个插件模块"""
        spec = importlib.util.spec_from_file_location(
            f"plugins.{module_name}", init_file
        )
        if not spec or not spec.loader:
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 查找 Plugin 类
        plugin_class = getattr(module, "Plugin", None)
        if not plugin_class or not issubclass(plugin_class, BasePlugin):
            logger.warning(f"插件 '{module_name}' 未找到有效的 Plugin 类")
            return None
        
        return plugin_class()
    
    async def activate_plugin(self, name: str) -> bool:
        """激活插件"""
        info = self._plugins.get(name)
        if not info:
            logger.warning(f"插件 '{name}' 未找到")
            return False
        
        if info.is_active:
            return True
        
        try:
            await info.plugin.activate()
            info.is_active = True
            logger.info(f"插件 '{name}' 已激活")
            return True
        except Exception as e:
            logger.error(f"激活插件 '{name}' 失败: {e}")
            return False
    
    async def deactivate_plugin(self, name: str) -> bool:
        """停用插件"""
        info = self._plugins.get(name)
        if not info or not info.is_active:
            return False
        
        try:
            await info.plugin.deactivate()
            info.is_active = False
            logger.info(f"插件 '{name}' 已停用")
            return True
        except Exception as e:
            logger.error(f"停用插件 '{name}' 失败: {e}")
            return False
    
    async def activate_all(self) -> int:
        """激活所有已发现的插件"""
        count = 0
        for name in self._plugins:
            if await self.activate_plugin(name):
                count += 1
        return count
    
    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self._plugins.get(name)
    
    def list_plugins(self) -> list[PluginInfo]:
        """列出所有插件"""
        return list(self._plugins.values())
    
    def list_active_plugins(self) -> list[PluginInfo]:
        """列出所有已激活的插件"""
        return [p for p in self._plugins.values() if p.is_active]
