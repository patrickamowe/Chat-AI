# app/utils/auth.py
import hashlib
from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from pwdlib import PasswordHash
from typing import Optional

from ..core.config import settings
from ..schemas.auth import AccessTokenJWTPayload, RefreshTokenJWTPayload

# Initialize password hashing and token extraction setups
password_hash = PasswordHash.recommended()

# auto_error=False stops FastAPI from automatically throwing a generic 401 error
# when a token is missing. This allows our routes to handle the error cleanly.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain-text password matches the scrambled hash stored in the database.
    """
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Turns a plain-text password into a secure cryptographic hash before database storage.
    """
    return password_hash.hash(password)


def hash_token(token: str) -> str:
    """
    Hashes a JWT token string using SHA-256 so we can store or look it up securely in the database.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: dict) -> str:
    """
    Generates a short-lived access token that keeps the user authenticated for immediate API requests.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_ACCESS_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """
    Generates a long-lived refresh token used exclusively to request new access tokens when they expire.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"user_id": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[AccessTokenJWTPayload]:
    """
    FastAPI dependency that reads and decodes the user's access token from the request header.

    Returns the user data payload if valid, or None if the token is missing or broken.
    """
    if not token:
        return None
    try:
        pay_load = jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return AccessTokenJWTPayload(**pay_load)
    except (InvalidTokenError, ValidationError):
        return None


async def validate_refresh_token(token: str) -> RefreshTokenJWTPayload :
    """
    Decodes an incoming refresh token string and extracts the user's data.

    Return user's data.
    If the token is expired or altered, it throws an error that our route's
    try-except block can catch instantly.
    """
    pay_load = jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM])

    return  RefreshTokenJWTPayload(**pay_load)

async def validate_access_token(token: str) -> AccessTokenJWTPayload :
    """
    Decodes an incoming access token string and extracts the user's data.

    Return user's data
    If the token is expired or altered, it throws an error that our route's
    try-except block can catch instantly.
    """
    pay_load = jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return  AccessTokenJWTPayload(**pay_load)