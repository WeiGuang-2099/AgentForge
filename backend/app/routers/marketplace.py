"""模板市场路由"""
import os
import yaml
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

PRESETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "presets")


class TemplateInfo(BaseModel):
    name: str
    display_name: str
    description: str
    model: str
    tools: list[str]
    is_team: bool


class TemplateExportResponse(BaseModel):
    name: str
    yaml_content: str


@router.get("/marketplace/templates", response_model=list[TemplateInfo])
async def list_templates():
    """列出所有可用模板"""
    templates = []
    presets_dir = os.path.normpath(PRESETS_DIR)
    
    # 单 Agent 模板
    if os.path.isdir(presets_dir):
        for f in os.listdir(presets_dir):
            if f.endswith((".yaml", ".yml")) and os.path.isfile(os.path.join(presets_dir, f)):
                try:
                    with open(os.path.join(presets_dir, f), "r", encoding="utf-8") as fh:
                        data = yaml.safe_load(fh)
                    if data:
                        templates.append(TemplateInfo(
                            name=data.get("name", ""),
                            display_name=data.get("display_name", data.get("name", "")),
                            description=data.get("description", ""),
                            model=data.get("model", ""),
                            tools=data.get("tools", []),
                            is_team=data.get("mode") == "team",
                        ))
                except:
                    pass
    
    # 团队模板
    team_dir = os.path.join(presets_dir, "team")
    if os.path.isdir(team_dir):
        for f in os.listdir(team_dir):
            if f.endswith((".yaml", ".yml")):
                try:
                    with open(os.path.join(team_dir, f), "r", encoding="utf-8") as fh:
                        data = yaml.safe_load(fh)
                    if data:
                        templates.append(TemplateInfo(
                            name=data.get("name", ""),
                            display_name=data.get("display_name", data.get("name", "")),
                            description=data.get("description", ""),
                            model="",
                            tools=[],
                            is_team=True,
                        ))
                except:
                    pass
    
    return templates


@router.get("/marketplace/templates/{name}/export", response_model=TemplateExportResponse)
async def export_template(name: str):
    """导出模板 YAML"""
    presets_dir = os.path.normpath(PRESETS_DIR)
    
    # 搜索单 Agent 和团队模板
    for search_dir in [presets_dir, os.path.join(presets_dir, "team")]:
        if not os.path.isdir(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f.endswith((".yaml", ".yml")):
                filepath = os.path.join(search_dir, f)
                with open(filepath, "r", encoding="utf-8") as fh:
                    content = fh.read()
                    data = yaml.safe_load(content)
                    if data and data.get("name") == name:
                        return TemplateExportResponse(name=name, yaml_content=content)
    
    raise HTTPException(status_code=404, detail=f"Template '{name}' not found")


@router.post("/marketplace/templates/import")
async def import_template(file: UploadFile = File(...)):
    """导入模板 YAML 文件"""
    if not file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(status_code=400, detail="Only YAML files are supported")
    
    content = await file.read()
    try:
        data = yaml.safe_load(content.decode("utf-8"))
    except:
        raise HTTPException(status_code=400, detail="Invalid YAML format")
    
    if not data or "name" not in data:
        raise HTTPException(status_code=400, detail="Template must contain a 'name' field")
    
    # 保存到 presets 目录
    presets_dir = os.path.normpath(PRESETS_DIR)
    if data.get("mode") == "team":
        save_dir = os.path.join(presets_dir, "team")
    else:
        save_dir = presets_dir
    
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, f"{data['name']}.yaml")
    with open(filepath, "wb") as f:
        f.write(content)
    
    return {"message": f"Template '{data['name']}' imported successfully", "name": data["name"]}
