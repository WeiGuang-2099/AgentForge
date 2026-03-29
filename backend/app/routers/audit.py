"""审计日志路由"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.database import get_db
from app.models.audit_log import AuditLog
from app.core.auth import get_current_user

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    detail: Optional[str]
    created_at: str


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询审计日志"""
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        AuditLogResponse(
            id=str(l.id),
            user_id=str(l.user_id) if l.user_id else None,
            action=l.action,
            resource_type=l.resource_type,
            resource_id=l.resource_id,
            detail=l.detail,
            created_at=l.created_at.isoformat() if l.created_at else "",
        )
        for l in logs
    ]
