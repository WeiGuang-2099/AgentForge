"""AgentForge API - 主入口"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.agent import AgentEngine
from app.core.workflow import WorkflowEngine
from app.plugins import PluginManager
from app.routers import agent, apikey, audit, auth, chat, marketplace, tool, usage, ws, workflow, plugin
from app.tools import register_all_tools
from app.models.database import init_db, close_db

# 配置日志
logging.basicConfig(level=logging.DEBUG if settings.APP_DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

# 全局 AgentEngine 实例
engine = AgentEngine()

# 全局 WorkflowEngine 实例
workflow_engine = WorkflowEngine(engine)

# 全局 PluginManager 实例
plugin_manager = PluginManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("AgentForge API starting...")
    # 注册所有工具
    register_all_tools()
    logger.info("All tools registered")
    # 初始化 Agent 引擎（加载预置模板）
    await engine.initialize()
    logger.info(f"Loaded {len(engine.list_agents())} agents")
    # 加载团队工作流预设
    presets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "presets")
    wf_count = workflow_engine.load_team_presets(os.path.normpath(presets_dir))
    logger.info(f"Loaded {wf_count} team workflows")
    # 发现并激活插件
    plugin_count = plugin_manager.discover_plugins()
    active_count = await plugin_manager.activate_all()
    logger.info(f"Discovered {plugin_count} plugins, activated {active_count}")
    # 初始化数据库表
    await init_db()
    logger.info("Database initialized")
    yield
    # 关闭数据库连接
    await close_db()
    logger.info("AgentForge API shutting down")

app = FastAPI(
    title="AgentForge API",
    description="Ready-to-use multi-agent collaboration framework",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(agent.router, prefix="/api", tags=["agents"])
app.include_router(apikey.router, prefix="/api", tags=["apikeys"])
app.include_router(audit.router, prefix="/api", tags=["audit"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(marketplace.router, prefix="/api", tags=["marketplace"])
app.include_router(tool.router, prefix="/api", tags=["tools"])
app.include_router(usage.router, prefix="/api", tags=["usage"])
app.include_router(workflow.router, prefix="/api", tags=["workflows"])
app.include_router(plugin.router, prefix="/api", tags=["plugins"])
app.include_router(ws.router, tags=["websocket"])

@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "agents_loaded": len(engine.list_agents()),
    }

def get_engine() -> AgentEngine:
    """获取全局 AgentEngine 实例（供路由使用）"""
    return engine

def get_workflow_engine() -> WorkflowEngine:
    """获取全局 WorkflowEngine 实例（供路由使用）"""
    return workflow_engine

def get_plugin_manager() -> PluginManager:
    """获取全局 PluginManager 实例（供路由使用）"""
    return plugin_manager
