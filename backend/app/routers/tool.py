"""工具管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.tools.base import tool_registry

router = APIRouter()


class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: list[dict]

class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: dict = {}

class ToolExecuteResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None


@router.get("/tools", response_model=list[ToolInfo])
async def list_tools():
    """列出所有可用工具"""
    tools = tool_registry.list_all()
    return [
        ToolInfo(
            name=t.name,
            description=t.description,
            parameters=[
                {"name": p.name, "type": p.type, "description": p.description, "required": p.required}
                for p in t.parameters
            ],
        )
        for t in tools
    ]

@router.post("/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(req: ToolExecuteRequest):
    """手动触发工具执行（调试用）"""
    from app.core.tool_runner import ToolRunner
    runner = ToolRunner()
    result = await runner.execute_tool_call(req.tool_name, req.arguments)
    return ToolExecuteResponse(
        success=result.success,
        output=result.output,
        error=result.error,
    )
