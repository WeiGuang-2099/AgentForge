"""API Key 管理路由"""
import re
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.api_key import UserApiKey
from app.utils.crypto import encrypt, decrypt, get_key_hint
from app.core.auth import get_current_user

router = APIRouter()


API_KEY_PATTERNS = {
    "openai": r"^sk-[a-zA-Z0-9_-]{20,}$",
    "anthropic": r"^sk-ant-[a-zA-Z0-9_-]{20,}$",
    "google": r"^AI[a-zA-Z0-9_-]{35,}$",
    "zhipuai": r"^[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}$",
    "deepseek": r"^sk-[a-zA-Z0-9]{20,}$",
    "moonshot": r"^sk-[a-zA-Z0-9]{20,}$",
}


def validate_api_key_format(provider: str, key: str) -> bool:
    """Validate API key format based on provider-specific patterns."""
    pattern = API_KEY_PATTERNS.get(provider.lower())
    if pattern:
        return bool(re.match(pattern, key))
    # For unknown providers, require minimum length of 20
    return len(key) >= 20


class ApiKeyCreateRequest(BaseModel):
    provider: str  # openai, anthropic, google
    api_key: str


class ApiKeyResponse(BaseModel):
    id: str
    provider: str
    key_hint: str
    is_valid: bool


class ApiKeyValidateResponse(BaseModel):
    provider: str
    is_valid: bool
    message: str


@router.get("/apikeys", response_model=list[ApiKeyResponse])
async def list_api_keys(user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserApiKey).where(UserApiKey.user_id == user_id))
    keys = result.scalars().all()
    return [ApiKeyResponse(id=str(k.id), provider=k.provider, key_hint=k.key_hint, is_valid=k.is_valid) for k in keys]


@router.post("/apikeys", response_model=ApiKeyResponse)
async def save_api_key(req: ApiKeyCreateRequest, user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 检查是否已存在该提供商的 key，存在则更新
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == user_id, UserApiKey.provider == req.provider)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.encrypted_key = encrypt(req.api_key)
        existing.key_hint = get_key_hint(req.api_key)
        existing.is_valid = True
        await db.commit()
        from app.utils.audit import log_audit
        await log_audit(db, action="save_api_key", user_id=user_id, resource_type="api_key", detail=f"Saved {req.provider} key")
        return ApiKeyResponse(id=str(existing.id), provider=existing.provider, key_hint=existing.key_hint, is_valid=True)
    
    key = UserApiKey(
        user_id=user_id,
        provider=req.provider,
        encrypted_key=encrypt(req.api_key),
        key_hint=get_key_hint(req.api_key),
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    from app.utils.audit import log_audit
    await log_audit(db, action="save_api_key", user_id=user_id, resource_type="api_key", detail=f"Saved {req.provider} key")
    return ApiKeyResponse(id=str(key.id), provider=key.provider, key_hint=key.key_hint, is_valid=key.is_valid)


@router.delete("/apikeys/{key_id}")
async def delete_api_key(key_id: str, user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserApiKey).where(UserApiKey.id == key_id, UserApiKey.user_id == user_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    await db.delete(key)
    await db.commit()
    from app.utils.audit import log_audit
    await log_audit(db, action="delete_api_key", user_id=user_id, resource_type="api_key", detail=f"Deleted key {key_id}")
    return {"message": "Deleted"}


@router.post("/apikeys/{key_id}/validate", response_model=ApiKeyValidateResponse)
async def validate_api_key(key_id: str, user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """验证 API Key 有效性（简单检查格式）"""
    result = await db.execute(select(UserApiKey).where(UserApiKey.id == key_id, UserApiKey.user_id == user_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    decrypted = decrypt(key.encrypted_key)
    is_valid = validate_api_key_format(key.provider, decrypted)
    key.is_valid = is_valid
    await db.commit()
    if is_valid:
        return ApiKeyValidateResponse(provider=key.provider, is_valid=True, message="Key format is valid")
    return ApiKeyValidateResponse(
        provider=key.provider,
        is_valid=False,
        message=f"API key format does not match expected pattern for provider: {key.provider}",
    )
