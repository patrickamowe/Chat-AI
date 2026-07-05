import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from pwdlib import PasswordHash

from ..core.config import settings
from ..schemas.auth import AccessTokenJWTPayload, RefreshTokenJWTPayload

# Initialize password hashing and token lookup setup
password_hash = PasswordHash.recommended()

# auto_error=False stops FastAPI from automatically throwing a generic 401 error
# when a token is missing. This lets us use our own clean error messages.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain-text password matches the hashed password from the database.

    Args:
        plain_password (str): The raw password entered by the user.
        hashed_password (str): The hashed password stored in the database.

    Returns:
        bool: True if they match, False if they do not.
    """
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password so it can be safely stored.

    Run this on user passwords before saving them to the database.

    Args:
        password (str): The raw password string to hash.

    Returns:
        str: The secure hashed version of the password.
    """
    return password_hash.hash(password)


def hash_token(token: str) -> str:
    """
    Hashes a JWT string using SHA-256 for safe database storage and lookup.

    This ensures that if the database is leaked, attackers cannot use the raw tokens.

    Args:
        token (str): The raw JWT token string.

    Returns:
        str: The secure hashed string.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: dict) -> str:
    """
    Generates a short-lived access token for API requests.

    Adds an expiration time to the payload based on your settings before signing it.

    Args:
        data (dict): The payload data (usually containing user_id and username).

    Returns:
        str: The signed and encoded JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_ACCESS_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """
    Generates a long-lived refresh token used to get new access tokens.

    Args:
        user_id (int): The ID of the user owning the session.

    Returns:
        str: The signed and encoded JWT refresh token.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=1)
    to_encode = {"user_id": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> AccessTokenJWTPayload:
    """
    Decodes an access token and verifies its signature.

    Args:
        token (str): The raw access token string.

    Raises:
        InvalidTokenError: If the token is invalid or expired.
        ValidationError: If the token data does not match the Pydantic schema.

    Returns:
        AccessTokenJWTPayload: The verified and parsed token data.
    """
    pay_load = jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return AccessTokenJWTPayload(**pay_load)


def validate_access_token(token: str) -> AccessTokenJWTPayload:
    """
    Validates an incoming access token and extracts the user data.

    Args:
        token (str): The raw access token string.

    Raises:
        InvalidTokenError: If the token is invalid or expired.
        ValidationError: If the token data is malformed.

    Returns:
        AccessTokenJWTPayload: The verified user data payload.
    """
    return decode_access_token(token)


def validate_refresh_token(token: str) -> RefreshTokenJWTPayload:
    """
    Validates an incoming refresh token and extracts the user ID.

    Args:
        token (str): The raw refresh token string.

    Raises:
        InvalidTokenError: If the token is invalid or expired.
        ValidationError: If the token data is malformed.

    Returns:
        RefreshTokenJWTPayload: The verified refresh payload.
    """
    pay_load = jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return RefreshTokenJWTPayload(**pay_load)


async def get_current_user(
        token: Optional[str] = Depends(oauth2_scheme)
) -> AccessTokenJWTPayload:
    """
    FastAPI dependency that requires a user to be logged in.

    Checks the access token from the request headers. If it is missing, expired,
    or invalid, it stops the request and returns an HTTP 401 Unauthorized error.

    Args:
        token (Optional[str]): The token extracted from the request headers.

    Raises:
        HTTPException: 401 Unauthorized if authentication fails.

    Returns:
        AccessTokenJWTPayload: The verified user data.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided."
        )

    try:
        return decode_access_token(token)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is invalid or has expired. Please sign in again."
        )


async def get_current_user_optional(
        token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[AccessTokenJWTPayload]:
    """
    FastAPI dependency that allows optional authentication.

    Useful for guest requests. If the token is missing or invalid, it returns None
    instead of throwing an error.

    Args:
        token (Optional[str]): The token extracted from the request headers.

    Returns:
        Optional[AccessTokenJWTPayload]: User data if logged in, otherwise None.
    """
    if not token:
        return None

    try:
        return decode_access_token(token)
    except (InvalidTokenError, ValidationError):
        return None