from pydantic import BaseModel, ConfigDict
from typing import Optional, Any

class AuthenticatedUserFields(BaseModel):
    """Basic user profile data that is completely safe to show on the frontend dashboard."""
    id: int
    username: str
    email: Optional[str] = None

class UserProfileResponseData(BaseModel):
    """The public profile information safe to return to the client after lookup or registration."""
    id: int
    username: str
    email: str
    # If your SQLAlchemy model has a created_at timestamp, you can add it here:
    # created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponseData(BaseModel):
    """The complete package returned after logging in: both secure tokens and the user profile."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: AuthenticatedUserFields


class TokenRefreshResponseData(BaseModel):
    """The brand-new access token pair generated during a background token refresh swap."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class APIBaseSuccessEnvelope(BaseModel):
    """Master success wrapper. Every successful API response in the app follows this exact shape."""
    status_code: int
    success: bool
    content: Optional[Any] = None
    message: str


class UserLoginSuccessEnvelope(APIBaseSuccessEnvelope):
    """Success response specifically for a successful sign-in. Holds token data and user metadata."""
    content: LoginResponseData

class UserRegistrationSuccessEnvelope(APIBaseSuccessEnvelope):
    """Success response wrapper for a newly created user account."""
    content: UserProfileResponseData

class UserProfileFetchSuccessEnvelope(APIBaseSuccessEnvelope):
    """Success response wrapper for pulling a specific user's account details."""
    content: UserProfileResponseData

class TokenRefreshSuccessEnvelope(APIBaseSuccessEnvelope):
    """Success response specifically for token renewals. Holds the fresh token package."""
    content: TokenRefreshResponseData


class UserLogoutSuccessEnvelope(APIBaseSuccessEnvelope):
    """Success response specifically for logouts. Returns no extra content data."""
    content: Optional[None] = None


class APIFailureEnvelope(BaseModel):
    """Master error wrapper. Every failed or denied API request follows this exact shape."""
    status_code: int
    success: bool
    message: str