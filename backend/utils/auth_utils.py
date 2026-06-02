import hashlib
from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from pwdlib import PasswordHash

from ..core.config import settings
from ..schemas.token_schema import AccessTokenPayload, RefreshTokenPayload

# Initialize authentication components
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")

# Reusable HTTP Exceptions
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expire access token",
    headers={"WWW-Authenticate": "Bearer"},
)

refresh_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid or expired refresh token",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if a plain text password matches its stored cryptographic hash."""
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a secure cryptographic hash from a plain text password."""
    return password_hash.hash(password)


def hash_token(token: str) -> str:
    """Hash a token using SHA-256 for secure, fast database lookup and storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: dict) -> str:
    """Create a short-lived JWT access token encoded with the access secret key."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.JWT_ACCESS_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived JWT refresh token encoded with the refresh secret key.

    Contains a minimal payload using the standard 'sub' claim for maximum security.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> AccessTokenPayload:
    """FastAPI dependency to extract, decode, and validate an incoming access token.

    Returns the parsed Pydantic payload containing user session identity data.
    """
    try:
        pay_load = jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return AccessTokenPayload(**pay_load)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception


async def validate_refresh_token(token: str) -> int:
    """Decode and validate a long-lived refresh token string.

    Returns the user ID as an integer if valid, otherwise raises a 401 Unauthorized exception.
    """
    try:
        pay_load = jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM])
        token_data = RefreshTokenPayload(**pay_load)
        return int(token_data.sub)
    except (InvalidTokenError, ValidationError, ValueError):
        raise refresh_exception