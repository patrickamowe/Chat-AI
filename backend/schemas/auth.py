from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from .base import APIBaseSuccessEnvelope

# --- REQUEST SCHEMAS ---
class UserRegistrationRequest(BaseModel):
    """The registration form data sent by a new user trying to create an account."""
    username: str
    password: str
    email: EmailStr

class UserLoginRequest(BaseModel):
    """Data sent by the frontend login form."""
    username: str
    password: str

class TokenRefreshRequest(BaseModel):
    """Data sent when requesting a new Access Token using a Refresh Token."""
    refresh_token: str

class TokenValidationRequest(BaseModel):
    """Data sent by the frontend to validate an Access Token."""
    access_token: str

class AccessTokenJWTPayload(BaseModel):
    """Data extracted from a valid Access Token."""
    user_id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class RefreshTokenJWTPayload(BaseModel):
    """Data extracted from a Refresh Token."""
    user_id: int


# --- RESPONSE DATA SHAPES ---

class AuthenticatedUserFields(BaseModel):
    """Basic user profile data safe to show on frontend dashboards."""
    id: int
    username: str
    email: Optional[str] = None

class UserProfileResponseData(BaseModel):
    """Public profile data safe to return after lookup or registration."""
    id: int
    username: str
    email: str
    model_config = ConfigDict(from_attributes=True)

class LoginResponseData(BaseModel):
    """Complete package returned after a successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: AuthenticatedUserFields

class TokenRefreshResponseData(BaseModel):
    """Brand-new token pair generated during a background renewal swap."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

class ValidAccessTokenResponseData(BaseModel):
    """Response returned when an access token is validated successfully."""
    valid: bool
    user: AuthenticatedUserFields


# --- FINAL ENVELOPES ---
class UserLoginSuccessEnvelope(APIBaseSuccessEnvelope):
    content: LoginResponseData

class UserRegistrationSuccessEnvelope(APIBaseSuccessEnvelope):
    content: UserProfileResponseData

class UserProfileFetchSuccessEnvelope(APIBaseSuccessEnvelope):
    content: UserProfileResponseData

class TokenRefreshSuccessEnvelope(APIBaseSuccessEnvelope):
    content: TokenRefreshResponseData

class ValidAccessTokenSuccessEnvelope(APIBaseSuccessEnvelope):
    content: ValidAccessTokenResponseData

class UserLogoutSuccessEnvelope(APIBaseSuccessEnvelope):
    content: Optional[None] = None