"""插件管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class PluginInfoResponse(BaseModel):
    name: str
    version: str
    description: str
    author: str
    is_active: bool


@router.get("/plugins", response_model=list[PluginInfoResponse])
async def list_plugins():
    from app.main import get_plugin_manager
    manager = get_plugin_manager()
    return [
        PluginInfoResponse(
            name=p.metadata.name,
            version=p.metadata.version,
            description=p.metadata.description,
            author=p.metadata.author,
            is_active=p.is_active,
        )
        for p in manager.list_plugins()
    ]


@router.post("/plugins/{name}/activate")
async def activate_plugin(name: str):
    from app.main import get_plugin_manager
    manager = get_plugin_manager()
    success = await manager.activate_plugin(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found or activation failed")
    return {"message": f"Plugin '{name}' activated"}


@router.post("/plugins/{name}/deactivate")
async def deactivate_plugin(name: str):
    from app.main import get_plugin_manager
    manager = get_plugin_manager()
    success = await manager.deactivate_plugin(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found or deactivation failed")
    return {"message": f"Plugin '{name}' deactivated"}
