from pydantic import BaseModel
from typing import Optional, Any

class APIBaseSuccessEnvelope(BaseModel):
    """Master success wrapper. Every successful API response follows this shape."""
    status_code: int
    success: bool = True
    message: str
    content: Optional[Any] = None

class APIFailureEnvelope(BaseModel):
    """Master error wrapper. Every failed or denied API request follows this shape."""
    status_code: int
    success: bool = False
    message: str