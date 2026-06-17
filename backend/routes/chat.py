from datetime import datetime
from fastapi import APIRouter, Depends, status, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from ..db.database import get_db
from ..models.model import Conversation, Message, User
from ..schemas.auth import AccessTokenJWTPayload
from ..schemas.base import APIFailureEnvelope
from ..schemas.chat import (
    ConversationDeleteSuccessEnvelope,
    ConversationDetailsSuccessEnvelope,
    ConversationsDeleteSuccessEnvelope,
    ConversationsListSuccessEnvelope,
    MessageResponseData,
    MessageSendSuccessEnvelope,
    SendMessageRequest,
    ConversationInfo,
    MessageRecord,
    AssistantResponse
)
from google.genai import types
from pydantic import ValidationError
from ..utils.auth import get_current_user
from ..utils.gemini import client


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/message",
    response_model=MessageSendSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Send a Chat Message",
    responses={
        400: {
            "model": APIFailureEnvelope,
            "description": "Bad Request: Invalid or missing parameter combinations.",
        },
        404: {
            "model": APIFailureEnvelope,
            "description": "Not Found: User or conversation does not exist.",
        },
        500: {
            "model": APIFailureEnvelope,
            "description": "Internal Server Error: Database or server error.",
        },
        502: {
            "model": APIFailureEnvelope,
            "description": "Bad Gateway: Gemini AI failed to return a response or invalid JSON schema layout."
        },
    },
)
def send_message(
        message_request: SendMessageRequest,
        db: Session = Depends(get_db),
        auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user),
):
    """
    Handles sending chat messages and routes them into one of three cases:
    1. Guest Chat (No auth token present; volatile context)
    2. Existing Chat (Valid auth token and conversation_id match; appended to history)
    3. New Chat (Valid auth token provided, conversation_id is null; creates a thread)
    """
    user_prompt = message_request.user_prompt
    conversation_id = message_request.conversation_id
    timestamp_str = str(datetime.utcnow())
    user_id = auth_user.user_id if auth_user else None

    user = None
    gemini_contents = []

    # --- PHASE 1: EARLY VALIDATION & HISTORY RETRIEVAL ---
    if user_id is not None:
        # Validate User early to avoid redundant queries later
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="User account could not be found.",
                ).model_dump(mode="json")
            )

        # CASE 2: Existing Conversation - Fetch history context
        if conversation_id is not None:
            conversation = (
                db.query(Conversation)
                .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
                .first()
            )
            if not conversation:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=APIFailureEnvelope(
                        status_code=status.HTTP_404_NOT_FOUND,
                        success=False,
                        message="Conversation thread could not be found.",
                    ).model_dump(mode="json")
                )

            # Pull last 10 records (newest first) to build the chat timeline
            db_messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.id.desc())
                .limit(10)
                .all()
            )
            db_messages.reverse()  # Reverse to restore correct chronological order

            for msg in db_messages:
                gemini_contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg.user_prompt)]))
                if msg.AI_response:
                    gemini_contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg.user_prompt)]))

    # Append the incoming current user_prompt text to the end of the payload list
    gemini_contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))

    # --- PHASE 2: AI GENERATION & PARSING ---
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=gemini_contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AssistantResponse,
                system_instruction=(
                    "You are an expert assistant. Your responses in the 'content' field "
                    "must be thorough, highly detailed, and elegantly styled using rich Markdown. "
                    "Avoid brief summaries or skipping explanations."
                ),
            ),
        )
        raw_text = response.text

        if not raw_text:
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    success=False,
                    message="The AI engine returned an empty response.",
                ).model_dump(mode="json")
            )

        # Map JSON back to Pydantic object cleanly
        ai_response = AssistantResponse.model_validate_json(raw_text)

    except ValidationError:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=APIFailureEnvelope(
                status_code=status.HTTP_502_BAD_GATEWAY,
                success=False,
                message="AI engine returned invalid structured layout data format.",
            ).model_dump(mode="json")
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"AI connection failure: {str(e)}",
            ).model_dump(mode="json")
        )

    # --- PHASE 3: CASE ROUTING & EXECUTION ---

    # CASE 1: GUEST CHAT
    if user_id is None:
        return MessageSendSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Temporary message processed successfully",
            content=MessageResponseData(
                user_prompt=user_prompt,
                AI_response=ai_response.content,
                created_at=timestamp_str
            ),
        )

    # CASES 2 & 3: AUTHENTICATED PERSISTENCE (Consolidated Transaction)
    try:
        if conversation_id is None:
            # Case 3: Create conversation master header entry
            title = getattr(ai_response, 'title', None)
            conversation = Conversation(
                user_id=user_id,
                title=str(title) if title else f"Chat with {user.username}",
            )
            db.add(conversation)
            db.flush()  # Extract the newly minted database primary ID reference
            conversation_id = conversation.id
            success_message = "New conversation created successfully"
        else:
            # Case 2: Existing Thread
            success_message = "Message added to conversation successfully"

        # Universal message insertion block
        message = Message(
            conversation_id=int(conversation_id),
            sender=str(user.username),
            user_prompt=user_prompt,
            AI_response=ai_response.content,
        )
        db.add(message)
        db.commit()
        db.refresh(message)

    except Exception as db_err:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Database pipeline failure: {str(db_err)}",
            ).model_dump(mode="json")
        )

    return MessageSendSuccessEnvelope(
        status_code=status.HTTP_200_OK,
        success=True,
        message=success_message,
        content=MessageResponseData(
            user_prompt=user_prompt,
            conversation_id=conversation_id,
            AI_response=ai_response.content,
            created_at=timestamp_str,
            sender=str(user.username),
        ),
    )

@router.get(
    "/conversations",
    response_model=ConversationsListSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Get All Conversations for Current User",
    responses={
        401: {
            "model": APIFailureEnvelope,
            "description": "Unauthorized: Missing or invalid token.",
        },
        404: {
            "model": APIFailureEnvelope,
            "description": "Not Found: User account not found.",
        },
        500: {
            "model": APIFailureEnvelope,
            "description": "Internal Server Error: Database failure.",
        },
    },
)
async def get_conversations(
        db: Session = Depends(get_db),
        auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user),
):
    """
    Gets a list of all conversations belonging to the logged-in user.
    Returns an empty list `[]` if the user has no history.
    """
    if not auth_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=APIFailureEnvelope(
                status_code=status.HTTP_401_UNAUTHORIZED,
                success=False,
                message="Authentication token is missing or expired.",
            ).model_dump(mode="json"),
        )

    user = db.query(User).filter(User.id == auth_user.user_id).first()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIFailureEnvelope(
                status_code=status.HTTP_404_NOT_FOUND,
                success=False,
                message="User account could not be found.",
            ).model_dump(mode="json"),
        )

    try:
        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.desc())
            .all()
        )

        formatted_conversations = [
            ConversationInfo(
                id=int(conversation.id),
                user_id=int(conversation.user_id),
                title=str(conversation.title),
                created_at=str(conversation.created_at)
            ).model_dump(mode="json") for conversation in conversations
        ]

        return ConversationsListSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User conversations fetched successfully.",
            content=formatted_conversations,
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Database error while fetching conversations: {str(e)}",
            ).model_dump(mode="json"),
        )


@router.delete(
    "/conversations",
    response_model=ConversationsDeleteSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Delete All Conversations for Current User",
    responses={
        401: {
            "model": APIFailureEnvelope,
            "description": "Unauthorized: Token validation failed.",
        },
        404: {
            "model": APIFailureEnvelope,
            "description": "Not Found: User account does not exist.",
        },
        500: {
            "model": APIFailureEnvelope,
            "description": "Internal Server Error: Database failure.",
        },
    },
)
async def delete_conversations(
        db: Session = Depends(get_db),
        auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user),
):
    """
    Permanently deletes all conversation history and messages for the logged-in user.
    All related messages are deleted automatically via model relationship constraints.
    """
    if not auth_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=APIFailureEnvelope(
                status_code=status.HTTP_401_UNAUTHORIZED,
                success=False,
                message="Authentication token is missing or invalid.",
            ).model_dump(mode="json")
        )

    user = db.query(User).filter(User.id == auth_user.user_id).first()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIFailureEnvelope(
                status_code=status.HTTP_404_NOT_FOUND,
                success=False,
                message="User account could not be found.",
            ).model_dump(mode="json")
        )

    try:
        db.query(Conversation).filter(Conversation.user_id == user.id).delete(
            synchronize_session=False
        )
        db.commit()

        return ConversationsDeleteSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="All conversations deleted for the user.",
        )

    except Exception as db_err:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Database error while deleting conversations: {str(db_err)}",
            ).model_dump(mode="json")
        )


@router.get(
    "/conversation/{conversation_id}",
    response_model=ConversationDetailsSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Get Messages from a Single Conversation",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Unauthorized"},
        404: {
            "model": APIFailureEnvelope,
            "description": "Not Found: Conversation does not exist.",
        },
        500: {
            "model": APIFailureEnvelope,
            "description": "Internal Server Error",
        },
    },
)
async def get_conversation(
        conversation_id: Annotated[int, Path(title="The ID of the conversation to get", ge=1)],
        db: Session = Depends(get_db),
        auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user),
):
    """
    Gets the full message history for a specific conversation ID.
    Validates that the logged-in user owns the conversation before returning data.
    """
    if not auth_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=APIFailureEnvelope(
                status_code=status.HTTP_401_UNAUTHORIZED,
                success=False,
                message="Authentication token is missing or invalid.",
            ).model_dump(mode="json"),
        )

    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="Conversation record could not be found.",
                ).model_dump(mode="json"),
            )

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .all()
        )

        formatted_message = [
            MessageRecord(
                id=int(message_record.id),
                conversation_id=int(message_record.conversation_id),
                sender=str(message_record.sender),
                user_prompt=str(message_record.user_prompt),
                AI_response=str(message_record.AI_response),
                created_at=str(message_record.created_at),
            ) for message_record in messages
        ]

        return ConversationDetailsSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Conversation messages loaded successfully.",
            content=formatted_message,
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Database error while loading conversation: {str(e)}",
            ).model_dump(mode="json"),
        )


@router.delete(
    "/conversation/{conversation_id}",
    response_model=ConversationDeleteSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Delete a Single Conversation",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Unauthorized"},
        404: {
            "model": APIFailureEnvelope,
            "description": "Not Found: Conversation does not exist.",
        },
        500: {
            "model": APIFailureEnvelope,
            "description": "Internal Server Error",
        },
    },
)
async def delete_conversation(
        conversation_id:Annotated[int, Path(title="The ID of the conversation to delete", ge=1)],
        db: Session = Depends(get_db),
        auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user),
):
    """
    Permanently deletes a single conversation by its ID.
    All associated messages are deleted automatically via model relationship constraints.
    """
    if not auth_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=APIFailureEnvelope(
                status_code=status.HTTP_401_UNAUTHORIZED,
                success=False,
                message="Authentication token is missing or invalid.",
            ).model_dump(mode="json")
        )

    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="Conversation not found.",
                ).model_dump(mode="json")
            )

        db.delete(conversation)
        db.commit()

        return ConversationDeleteSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Conversation deleted for the user.",
        )

    except Exception as db_err:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Database error while deleting conversation: {str(db_err)}",
            ).model_dump(mode="json")
        )