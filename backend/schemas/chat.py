from pydantic import BaseModel, Field
from typing import Optional, List
from .base import APIBaseSuccessSchema

# --- REQUEST SCHEMAS ---
class SendMessageRequestData(BaseModel):
    """Data sent by frontend when submitting a new message to the chat."""
    user_prompt: str
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None

class ConversationRenameRequestData(BaseModel):
    """Data sent by frontend when rename conversation."""
    title: str


# --- RESPONSE DATA SHAPES ---
class MessageResponseData(BaseModel):
    """The shape of a single message returned in live conversation loops."""
    id: Optional[int] = None
    sender: str = "anonymous"
    conversation_id: Optional[int] = None
    conversation_title: Optional[str]  = None
    user_prompt: str
    AI_response: str
    created_at: str

class ConversationInfo(BaseModel):
    id: int
    user_id: int
    title: str

class MessageInfo(BaseModel):
    id: int
    conversation_id: int
    sender: str
    user_prompt: str
    AI_response: str


# --- FINAL SCHEMAS ---
class MessageSendSuccessSchema(APIBaseSuccessSchema):
    content: MessageResponseData

class ConversationsListSuccessSchema(APIBaseSuccessSchema):
    content: List[ConversationInfo]

class ConversationsDeleteSuccessSchema(APIBaseSuccessSchema):
    content: Optional[None] = None

class ConversationDetailsSuccessSchema(APIBaseSuccessSchema):
    content: List[MessageInfo]

class ConversationDeleteSuccessSchema(APIBaseSuccessSchema):
    content: Optional[None] = None

class ConversationRenameSuccessSchema(APIBaseSuccessSchema):
    content: Optional[None] = None


class AssistantResponse(BaseModel):
    title: str = Field(
        description="A concise, 3-5 word title summarizing the user's initial request."
    )
    content: str = Field(
        description=(
            "The main response to the user. This MUST be a long, deeply detailed, "
            "and comprehensive answer. You must use full Markdown formatting "
            "including headers (##, ###), bullet points, bold text, and code blocks  e.t.c"
            "where appropriate. Do not return plain, short paragraphs."
        )
    )