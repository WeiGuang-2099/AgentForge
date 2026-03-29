"""Agent 管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# --- Pydantic Schemas ---

class AgentInfo(BaseModel):
    """Agent 信息响应"""
    name: str
    display_name: str
    description: str
    model: str
    tools: list[str]
    is_preset: bool

class AgentCreateRequest(BaseModel):
    """创建 Agent 请求"""
    name: str
    display_name: str
    description: str
    model: str = "gpt-4-turbo-preview"
    system_prompt: str
    tools: list[str] = []
    parameters: Optional[dict] = None

class AgentCreateResponse(BaseModel):
    name: str
    display_name: str
    message: str

# --- Routes ---

@router.get("/agents", response_model=list[AgentInfo])
async def list_agents():
    """列出所有可用 Agent"""
    from app.main import get_engine
    engine = get_engine()
    agents = engine.list_agents()
    return [
        AgentInfo(
            name=a.name,
            display_name=a.display_name,
            description=a.description,
            model=a.model,
            tools=a.tools,
            is_preset=a.is_preset,
        )
        for a in agents
    ]

@router.get("/agents/{name}", response_model=AgentInfo)
async def get_agent(name: str):
    """获取 Agent 详情"""
    from app.main import get_engine
    engine = get_engine()
    profile = engine.get_agent(name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' 未找到")
    return AgentInfo(
        name=profile.name,
        display_name=profile.display_name,
        description=profile.description,
        model=profile.model,
        tools=profile.tools,
        is_preset=profile.is_preset,
    )

@router.post("/agents", response_model=AgentCreateResponse)
async def create_agent(req: AgentCreateRequest):
    """创建自定义 Agent"""
    from app.main import get_engine
    from app.core.agent import AgentProfile
    engine = get_engine()
    
    # 检查名称是否已存在
    if engine.get_agent(req.name):
        raise HTTPException(status_code=409, detail=f"Agent '{req.name}' 已存在")
    
    profile = AgentProfile(
        name=req.name,
        display_name=req.display_name,
        description=req.description,
        model=req.model,
        system_prompt=req.system_prompt,
        tools=req.tools,
        parameters=req.parameters or {"temperature": 0.7, "max_tokens": 2000},
        is_preset=False,
    )
    await engine.create_agent(profile)
    return AgentCreateResponse(
        name=profile.name,
        display_name=profile.display_name,
        message="Agent 创建成功",
    )
