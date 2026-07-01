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

# Initialize password hashing and token extraction setups
password_hash = PasswordHash.recommended()

# auto_error=False stops FastAPI from automatically throwing a generic 401 error
# when a token is missing. This allows our custom dependencies to control exception structures.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain-text password matches the secure hash stored in the database.

    Args:
        plain_password (str): The raw plaintext password provided by the user.
        hashed_password (str): The stored bcrypt/argon2 hash from the database.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Transforms a plain-text password into a secure cryptographic hash.

    This should be executed on user credentials prior to persisting
    the user record to the database.

    Args:
        password (str): The raw plaintext password string to scramble.

    Returns:
        str: The secure cryptographically hashed representation of the password.
    """
    return password_hash.hash(password)


def hash_token(token: str) -> str:
    """
    Hashes a JWT token string using SHA-256 for secure database lookup and storage.

    This ensures that compromised databases do not leak functional, active JWT tokens.

    Args:
        token (str): The raw base64 JWT token string.

    Returns:
        str: A secure hexadecimal digest of the hashed token string.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: dict) -> str:
    """
    Generates a short-lived access token validating immediate API sessions.

    Appends a calculated UTC expiration timestamp based on environment configuration values
    to the token payload before signing it.

    Args:
        data (dict): The custom payload data (typically containing user_id and username).

    Returns:
        str: The fully signed and encoded JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_ACCESS_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """
    Generates a long-lived session refresh token used to request new access tokens.

    Args:
        user_id (int): The unique primary ID key of the user owning the session.

    Returns:
        str: The fully signed and encoded JWT refresh token.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=1)
    to_encode = {"user_id": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> AccessTokenJWTPayload:
    """
    Decodes and validates the signature of an incoming access token string.

    Args:
        token (str): The raw access token string.

    Raises:
        InvalidTokenError: If the token signature is broken, modified, or has expired.
        ValidationError: If the decoded payload fails model field schema validation.

    Returns:
        AccessTokenJWTPayload: The validated and parsed JWT access payload object.
    """
    pay_load = jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return AccessTokenJWTPayload(**pay_load)


def validate_access_token(token: str) -> AccessTokenJWTPayload:
    """
    Decodes an incoming access token string and extracts the user's data.

    Returns the user data if valid. If the token is expired or altered, it throws
    an error that route-level catch blocks or dependencies can capture.

    Args:
        token (str): The raw access token string.

    Raises:
        InvalidTokenError: If the signature is compromised or has expired.
        ValidationError: If payload schema checks fail.

    Returns:
        AccessTokenJWTPayload: The verified data payload.
    """
    return decode_access_token(token)


def validate_refresh_token(token: str) -> RefreshTokenJWTPayload:
    """
    Decodes an incoming refresh token string and extracts the associated user data.

    Returns the user data if valid. If the token is expired or altered, it throws
    an error that route-level catch blocks or dependencies can capture.

    Args:
        token (str): The raw refresh token string.

    Raises:
        InvalidTokenError: If the signature is compromised or has expired.
        ValidationError: If payload schema checks fail.

    Returns:
        RefreshTokenJWTPayload: The verified refresh data payload.
    """
    pay_load = jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return RefreshTokenJWTPayload(**pay_load)


async def get_current_user(
        token: Optional[str] = Depends(oauth2_scheme)
) -> AccessTokenJWTPayload:
    """
    FastAPI strict gateway dependency that mandates authentication.

    Verifies the client's Bearer access token. If the token is missing, expired,
    or structurally invalid, it immediately halts request processing and raises
    an HTTP 401 Unauthorized exception.

    Args:
        token (Optional[str]): The parsed Bearer token extracted from request headers.

    Raises:
        HTTPException: 401 Unauthorized if the credentials validation sequence fails.

    Returns:
        AccessTokenJWTPayload: The validated user identity details.
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
    FastAPI permissive dependency that allows optional authentication.

    Allows unauthenticated requests (such as guest chats) by returning None 
    rather than raising exceptions when token structures are missing or invalid.

    Args:
        token (Optional[str]): The parsed Bearer token extracted from request headers.

    Returns:
        Optional[AccessTokenJWTPayload]: Validated identity payload if authorized, otherwise None.
    """
    if not token:
        return None

    try:
        return decode_access_token(token)
    except (InvalidTokenError, ValidationError):
        return None