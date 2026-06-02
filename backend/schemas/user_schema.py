from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr

class UserSchema(BaseModel):
    username: str
    password: str
    email: EmailStr
    access_token: str | None = None
    refresh_token: str | None = None

class SigninSchema(BaseModel):
    username: str
    password: str

class GetUser(BaseModel):
    user_id: int
    username: str

    # Tells Pydantic how to read SQLAlchemy objects directly
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    # Tells Pydantic how to read SQLAlchemy objects directly
    model_config = ConfigDict(from_attributes=True)