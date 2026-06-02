from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """The schema returned to the client upon successful authentication."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    # Tells Pydantic how to read SQLAlchemy objects directly
    model_config = ConfigDict(from_attributes=True)


class AccessTokenPayload(BaseModel):
    """The decoded data structure inside a short-lived Access Token."""
    user_id: int
    username: str


class RefreshTokenPayload(BaseModel):
    """The decoded data structure inside a long-lived Refresh Token.

    We map 'sub' (subject) from the JWT claims directly to this field.
    """
    sub: str