from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Path, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from pydantic import TypeAdapter, ValidationError

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
from ..utils.auth import get_current_user, get_current_user_optional
from ..utils.gemini import client

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/message",
    response_model=MessageSendSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Send a chat prompt to the AI assistant",
    responses={
        404: {"model": APIFailureEnvelope, "description": "Target profile or history trace not found."},
        500: {"model": APIFailureEnvelope, "description": "Internal tracking framework or DB error."},
        502: {"model": APIFailureEnvelope, "description": "AI core returned empty or syntactically invalid schema mapping."}
    },
)
async def send_message(
    message_request: SendMessageRequest,
    db: Session = Depends(get_db),
    auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user_optional),
):
    """
    Evaluates and processes chat prompt requests against three execution trees:

    1. Guest Chat: Executed when no auth token is active. Responses are ephemeral.
    2. Existing Thread: Executed when auth matches and conversation_id is passed.
       Loads historical data context window directly into the generation layer.
    3. New Persistent Thread: Executed when auth matches but conversation_id is absent.
       Creates a permanent header object before executing data persistence workflows.

    Args:
        message_request (SendMessageRequest): Prompt string and explicit conversation indicators.
        db (Session): The database connection controller dependency.
        auth_user (Optional[AccessTokenJWTPayload]): Active session credentials, if present.

    Raises:
        HTTPException: 404 Not Found if user profiles or context IDs are missing.
        HTTPException: 502 Bad Gateway if Gemini models fail verification constraints.
        HTTPException: 500 Internal Error if persistence processing pipelines fail.

    Returns:
        MessageSendSuccessEnvelope: Packaged model block outlining prompt inputs and assistant metrics.
    """
    user_prompt = message_request.user_prompt
    conversation_id = message_request.conversation_id
    conversation_title = None
    timestamp_str = str(datetime.now(timezone.utc))
    user_id = auth_user.user_id if auth_user else None

    user = None
    gemini_contents = []

    # --- PHASE 1: EARLY VALIDATION & HISTORY RETRIEVAL ---
    if user_id is not None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account could not be located."
            )

        # CASE 2: Existing Conversation - Fetch history context safely bound to user
        if conversation_id is not None:
            conversation = (
                db.query(Conversation)
                .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
                .first()
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="The requested conversation thread could not be found or access is restricted."
                )

            # Pull last 10 records (newest first) to build context buffer
            db_messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.id.desc())
                .limit(10)
                .all()
            )
            db_messages.reverse()

            for msg in db_messages:
                gemini_contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg.user_prompt)]))
                if msg.AI_response:
                    # maps historical AI responses rather than replicating user prompts
                    gemini_contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg.AI_response)]))

    # Append current chat challenge parameters
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
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The AI engine failed to return valid content data structures."
            )

        ai_response = AssistantResponse.model_validate_json(raw_text)

    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI model response failed structural field configuration audits."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Core inference connection failure: {str(e)}"
        )

    # --- PHASE 3: CASE ROUTING & PERSISTENCE ---

    # CASE 1: GUEST CHAT (Short-circuit return)
    if user_id is None:
        return MessageSendSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Guest message processed successfully.",
            content=MessageResponseData(
                user_prompt=user_prompt,
                AI_response=ai_response.content,
                created_at=timestamp_str
            ),
        )

    # CASES 2 & 3: PERSISTENT TRANSACTION
    try:
        if conversation_id is None:
            # Case 3: Setup brand-new log container thread
            title = getattr(ai_response, 'title', None)
            conversation_title = str(title) if title else f"Conversation with {user.username}"
            conversation = Conversation(
                user_id=user_id,
                title=conversation_title,
            )
            db.add(conversation)
            db.flush()
            conversation_id = conversation.id
            success_message = "New conversation thread initialized successfully."
        else:
            success_message = "Message appended to active conversation successfully."

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database ledger entry insertion failure: {str(db_err)}"
        )

    return MessageSendSuccessEnvelope(
        status_code=status.HTTP_200_OK,
        success=True,
        message=success_message,
        content=MessageResponseData(
            user_prompt=user_prompt,
            conversation_id=conversation_id,
            conversation_title=conversation_title,
            AI_response=ai_response.content,
            created_at=timestamp_str,
            sender=str(user.username),
        ),
    )


@router.get(
    "/conversations",
    response_model=ConversationsListSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Get user conversation history logs",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "Target identity maps do not point to active users."},
        500: {"model": APIFailureEnvelope, "description": "Internal server database execution faults."}
    },
)
async def get_conversations(
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Compiles an organized trace of all historical chat headers tied to the active user profile.

    Args:
        db (Session): The database transaction manager engine.
        auth_user (AccessTokenJWTPayload): Security validation matrix.

    Raises:
        HTTPException: 404 Not Found if user trace is lost during query loops.
        HTTPException: 500 Internal Server Error on processing faults.

    Returns:
        ConversationsListSuccessEnvelope: An array listing tracking headers.
    """
    user = db.query(User).filter(User.id == auth_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account verification mapping was unresolvable."
        )

    try:
        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.asc())
            .all()
        )

        adapter = TypeAdapter(list[ConversationInfo])
        formatted_conversations = adapter.dump_python(conversations, mode="json")

        return ConversationsListSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User session historical traces compiled successfully.",
            content=formatted_conversations,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while compiling chat metrics: {str(e)}"
        )


@router.delete(
    "/conversations",
    response_model=ConversationsDeleteSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Wipe out user chat history",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "User matching records missing."},
        500: {"model": APIFailureEnvelope, "description": "Transaction processing error."}
    },
)
async def delete_conversations(
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Executes a complete metadata erasure of every chat tracking thread associated with the identity profile.

    Args:
        db (Session): Database active engine processing context.
        auth_user (AccessTokenJWTPayload): Credentials authorization layer.

    Raises:
        HTTPException: 404 Not Found if identity profile check drops out.
        HTTPException: 500 Internal Error during mass drop queries.

    Returns:
        ConversationsDeleteSuccessEnvelope: Clean database verification signal.
    """
    user = db.query(User).filter(User.id == auth_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User identity matching matrix validation failed."
        )

    try:
        db.query(Conversation).filter(Conversation.user_id == user.id).delete(
            synchronize_session=False
        )
        db.commit()

        return ConversationsDeleteSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="All historical conversation data records have been successfully deleted.",
        )

    except Exception as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing database clear request operations: {str(db_err)}"
        )


@router.get(
    "/conversation/{conversation_id}",
    response_model=ConversationDetailsSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Get conversation record logs",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "Conversation reference cannot be located."},
        500: {"model": APIFailureEnvelope, "description": "Internal data routing mapping faults."}
    },
)
async def get_conversation(
    conversation_id: Annotated[int, Path(title="The target conversation unique primary identifier", ge=1)],
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Extracts every granular chat message trace associated with a specific dialogue context container.

    Args:
        conversation_id (int): Database numerical primary tracking index.
        db (Session): Database operations layer dependency.
        auth_user (AccessTokenJWTPayload): Security validation framework payload.

    Raises:
        HTTPException: 404 Not Found if requested conversation index is unavailable or un-owned.
        HTTPException: 500 System Fault if transformation validation rules fail.

    Returns:
        ConversationDetailsSuccessEnvelope: Chronological dataset trace mapping previous interactions.
    """
    try:
        # filter validation guard confirming thread ownership matches auth context
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == auth_user.user_id)
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested conversation record does not exist or access was denied."
            )

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .all()
        )

        adapter = TypeAdapter(list[MessageRecord])
        formatted_messages = adapter.dump_python(messages, mode="json")

        return ConversationDetailsSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Dialogue timeline history records loaded successfully.",
            content=formatted_messages,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data pipeline system error while extracting timeline arrays: {str(e)}"
        )


@router.delete(
    "/conversation/{conversation_id}",
    response_model=ConversationDeleteSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Delete single conversation block",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "Specified tracking container missing."},
        500: {"model": APIFailureEnvelope, "description": "Database system mutation failure."}
    },
)
async def delete_conversation(
    conversation_id: Annotated[int, Path(title="The explicit identifier index aimed for drop commands", ge=1)],
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Destroys a separate individual dialogue stream header tracking container block.

    Args:
        conversation_id (int): Primary tracking container unique ID key.
        db (Session): Active system pipeline dependency context.
        auth_user (AccessTokenJWTPayload): Context configuration authorization tracking values.

    Raises:
        HTTPException: 404 Not Found if target ID is un-owned or invalid.
        HTTPException: 500 Transaction Error on internal database processing failure.

    Returns:
        ConversationDeleteSuccessEnvelope: Execution safety confirmation packet.
    """
    try:
        # filter criteria preventing cross-user account target access deletions
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == auth_user.user_id)
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The specified conversation thread target could not be found or access is restricted."
            )

        db.delete(conversation)
        db.commit()

        return ConversationDeleteSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Conversation record successfully purged from database histories.",
        )

    except HTTPException:
        raise
    except Exception as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database transaction failure executing clear request command routines: {str(db_err)}"
        )