"""Tests for authentication module (app.core.auth)."""
import pytest
from datetime import timedelta
from unittest.mock import patch

from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    ALGORITHM,
)
from app.config import settings
from jose import jwt
from fastapi import HTTPException


def test_hash_password():
    """hash_password returns a bcrypt hash, not plaintext."""
    password = "mysecretpassword"
    hashed = hash_password(password)
    assert hashed != password
    assert hashed.startswith("$2")  # bcrypt hashes start with $2b$ or $2a$


def test_verify_password_correct():
    """verify_password returns True for correct password."""
    password = "correctpassword"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """verify_password returns False for wrong password."""
    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    """creates a valid JWT with 'access' type and correct sub claim."""
    data = {"sub": "user123"}
    token = create_access_token(data)
    payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user123"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token():
    """creates a valid JWT with 'refresh' type."""
    data = {"sub": "user456"}
    token = create_refresh_token(data)
    payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user456"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token_valid():
    """decode_token returns correct payload for valid token."""
    data = {"sub": "user789"}
    token = create_access_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "user789"
    assert payload["type"] == "access"


def test_decode_token_expired():
    """decode_token raises HTTPException for expired token."""
    data = {"sub": "user_expired"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-10))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_decode_token_invalid():
    """decode_token raises HTTPException for garbage string."""
    with pytest.raises(HTTPException) as exc_info:
        decode_token("this.is.garbage")
    assert exc_info.value.status_code == 401
