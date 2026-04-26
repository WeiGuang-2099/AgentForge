"""插件管理路由"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

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


@router.get("/plugins/{name}")
async def get_plugin(name: str):
    from app.main import get_plugin_manager
    manager = get_plugin_manager()
    plugins = manager.list_plugins()
    plugin_info = None
    for p in plugins:
        if getattr(p.metadata, "name", None) == name:
            plugin_info = p
            break
    if not plugin_info:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    return PluginInfoResponse(
        name=plugin_info.metadata.name,
        version=plugin_info.metadata.version,
        description=plugin_info.metadata.description,
        author=plugin_info.metadata.author,
        is_active=plugin_info.is_active,
    )


@router.post("/plugins/{name}/activate")
async def activate_plugin(name: str, current_user = Depends(get_current_user)):
    from app.main import get_plugin_manager
    manager = get_plugin_manager()
    try:
        success = await manager.activate_plugin(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found or activation failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate plugin '{name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"Plugin '{name}' activated"}


@router.post("/plugins/{name}/deactivate")
async def deactivate_plugin(name: str, current_user = Depends(get_current_user)):
    from app.main import get_plugin_manager
    manager = get_plugin_manager()
    try:
        success = await manager.deactivate_plugin(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found or deactivation failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate plugin '{name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"Plugin '{name}' deactivated"}
