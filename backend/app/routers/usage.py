"""使用量统计路由"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.usage import UsageRecord
from app.core.auth import get_current_user

router = APIRouter()


class UsageSummary(BaseModel):
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int


class UsageByAgent(BaseModel):
    agent_name: str
    request_count: int
    total_tokens: int


class UsageByModel(BaseModel):
    model: str
    request_count: int
    total_tokens: int


@router.get("/usage/summary", response_model=UsageSummary)
async def get_usage_summary(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """获取总体使用量统计"""
    result = await db.execute(
        select(
            func.count(UsageRecord.id).label("count"),
            func.coalesce(func.sum(UsageRecord.prompt_tokens), 0).label("prompt"),
            func.coalesce(func.sum(UsageRecord.completion_tokens), 0).label("completion"),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0).label("total"),
        )
    )
    row = result.one()
    return UsageSummary(
        total_requests=row.count,
        total_prompt_tokens=row.prompt,
        total_completion_tokens=row.completion,
        total_tokens=row.total,
    )


@router.get("/usage/by-agent", response_model=list[UsageByAgent])
async def get_usage_by_agent(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """按 Agent 分组的使用量"""
    result = await db.execute(
        select(
            UsageRecord.agent_name,
            func.count(UsageRecord.id).label("count"),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0).label("total"),
        ).group_by(UsageRecord.agent_name)
    )
    return [UsageByAgent(agent_name=r.agent_name, request_count=r.count, total_tokens=r.total) for r in result.all()]


@router.get("/usage/by-model", response_model=list[UsageByModel])
async def get_usage_by_model(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """按模型分组的使用量"""
    result = await db.execute(
        select(
            UsageRecord.model,
            func.count(UsageRecord.id).label("count"),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0).label("total"),
        ).group_by(UsageRecord.model)
    )
    return [UsageByModel(model=r.model, request_count=r.count, total_tokens=r.total) for r in result.all()]
