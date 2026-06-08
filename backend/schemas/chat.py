from pydantic import BaseModel
from typing import Optional, List
from .base import APIBaseSuccessEnvelope

# --- REQUEST SCHEMAS ---
class SendMessageRequest(BaseModel):
    """Data sent by frontend when submitting a new message to the chat."""
    message: str
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None

class ConversationRequest(BaseModel):
    """Data sent by the frontend when targeting a single conversation."""
    conversation_id: int


# --- RESPONSE DATA SHAPES ---
class MessageResponseData(BaseModel):
    """The shape of a single message returned in live conversation loops."""
    id: Optional[int] = None
    sender: str = "anonymous"
    request: str
    response: str
    created_at: str

class ConversationsInfo(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: str

class MessageRecord(BaseModel):
    id: int
    conversation_id: int
    sender: str
    content: str
    response: str
    created_at: str


# --- FINAL ENVELOPES ---
class MessageSendSuccessEnvelope(APIBaseSuccessEnvelope):
    content: MessageResponseData

class ConversationsListSuccessEnvelope(APIBaseSuccessEnvelope):
    content: List[ConversationsInfo]

class ConversationsDeleteSuccessEnvelope(APIBaseSuccessEnvelope):
    content: Optional[None] = None

class ConversationDetailsSuccessEnvelope(APIBaseSuccessEnvelope):
    content: List[MessageRecord]

class ConversationDeleteSuccessEnvelope(APIBaseSuccessEnvelope):
    content: Optional[None] = None