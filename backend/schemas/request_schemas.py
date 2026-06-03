from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegistrationRequest(BaseModel):
    """The registration form data sent by a new user trying to create an account."""
    username: str
    password: str
    email: EmailStr

class UserLoginRequest(BaseModel):
    """Data sent by the frontend login form (Username + Password)."""
    username: str
    password: str


class AccessTokenJWTPayload(BaseModel):
    """Data extracted from a valid Access Token to identify who is making the request."""
    user_id: int
    username: str

    # Allows Pydantic to convert SQLAlchemy database rows directly into this schema
    model_config = ConfigDict(from_attributes=True)


class RefreshTokenJWTPayload(BaseModel):
    """Data extracted from a Refresh Token to find out which user owns the session."""
    sub: str  # The user's ID stored as a string inside the JWT 'subject' claim