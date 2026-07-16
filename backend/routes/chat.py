from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Path, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from pydantic import TypeAdapter, ValidationError

from ..db.database import get_db
from ..models.model import Conversation, Message, User
from ..schemas.auth import AccessTokenJWTPayload
from ..schemas.base import APIFailureSchema
from ..schemas.chat import (
    ConversationDeleteSuccessSchema,
    ConversationDetailsSuccessSchema,
    ConversationsDeleteSuccessSchema,
    ConversationsListSuccessSchema,
    ConversationRenameSuccessSchema,
    MessageResponseData,
    MessageSendSuccessSchema,
    SendMessageRequestData,
    ConversationInfo,
    MessageInfo,
    AssistantResponse,
    ConversationRenameRequestData
)
from google.genai import types
from ..utils.auth import get_current_user, get_current_user_optional
from ..utils.gemini import client

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/message",
    response_model=MessageSendSuccessSchema,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the AI assistant",
    responses={
        404: {"model": APIFailureSchema, "description": "User or conversation history not found."},
        500: {"model": APIFailureSchema, "description": "Internal server or database error."},
        502: {"model": APIFailureSchema, "description": "AI model returned an invalid response structure."}
    },
)
async def send_message(
    message_request: SendMessageRequestData,
    db: Session = Depends(get_db),
    auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user_optional),
):
    """
    Processes a user prompt using one of three workflows:

    1. Guest Chat: Active if no auth token is provided. Responses are not saved.
    2. Existing Thread: Active if user is logged in and passes a conversation_id.
       Loads the last 10 messages for context.
    3. New Thread: Active if user is logged in but conversation_id is missing.
       Creates a new conversation record in the database.

    Args:
        message_request (SendMessageRequestData): The user prompt and optional conversation ID.
        db (Session): Database session dependency.
        auth_user (Optional[AccessTokenJWTPayload]): Logged-in user data, if available.

    Raises:
        HTTPException: 404 Not Found if user or conversation doesn't exist.
        HTTPException: 502 Bad Gateway if the Gemini API response fails validation.
        HTTPException: 500 Internal Server Error if database saving fails.

    Returns:
        MessageSendSuccessSchema: The prompt, AI response, and conversation metadata.
    """
    user_prompt = message_request.user_prompt
    conversation_id = message_request.conversation_id
    conversation_title = None
    timestamp_str = str(datetime.now(timezone.utc))
    user_id = auth_user.user_id if auth_user else None

    user = None
    gemini_contents = []

    # --- PHASE 1: VALIDATION & HISTORY RETRIEVAL ---
    try:
        if user_id is not None:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User account could not be found."
                )

            # Handle existing conversations for logged-in users
            if conversation_id is not None:
                conversation = (
                    db.query(Conversation)
                    .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
                    .first()
                )
                if not conversation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="The requested conversation could not be found or access is denied."
                    )

                # Fetch last 10 messages to provide history context to the AI
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
                        gemini_contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg.AI_response)]))
    except HTTPException:
        raise
    except Exception as e:
        print("Database/Validation Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while retrieving user or history context."
        )

    # Append current user prompt
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

    except ValidationError as val_err:
        print("Pydantic Validation Error:", str(val_err))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI model response failed structural field configuration audits."
        )
    except HTTPException:
        raise
    except Exception as e:
        print("Inference System Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A core inference generation connection failure occurred."
        )

    # --- PHASE 3: SAVING DATA & RESPONDING ---

    # Workflow 1: Guest Chat (Return early, do not save to database)
    if user_id is None:
        return MessageSendSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Guest message processed successfully.",
            content=MessageResponseData(
                user_prompt=user_prompt,
                AI_response=ai_response.content,
                created_at=timestamp_str
            ),
        )

    # Workflow 2 & 3: Persistent Chat (Save to database)
    try:
        if conversation_id is None:
            # Workflow 3: Create a brand new conversation thread
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
        print("Database Transaction Error:", str(db_err))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database ledger entry insertion failure occurred while saving history threads."
        )

    return MessageSendSuccessSchema(
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
    response_model=ConversationsListSuccessSchema,
    status_code=status.HTTP_200_OK,
    summary="Get all conversations for the user",
    responses={
        401: {"model": APIFailureSchema, "description": "Invalid or missing access token."},
        404: {"model": APIFailureSchema, "description": "User account not found."},
        500: {"model": APIFailureSchema, "description": "Internal server database error."}
    },
)
async def get_conversations(
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Fetches a list of all historical conversations belonging to the authenticated user.

    Args:
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Authenticated user payload.

    Raises:
        HTTPException: 404 Not Found if user cannot be verified.
        HTTPException: 500 Internal Server Error if database query fails.

    Returns:
        ConversationsListSuccessSchema: A list of conversation records.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account could not be found."
            )

        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.asc())
            .all()
        )

        adapter = TypeAdapter(list[ConversationInfo])
        formatted_conversations = adapter.dump_python(conversations, mode="json")

        return ConversationsListSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User conversation history retrieved successfully.",
            content=formatted_conversations,
        )

    except HTTPException:
        raise
    except Exception as e:
        print("Fetch Conversations Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal database error occurred while compiling chat metrics."
        )


@router.delete(
    "/conversations",
    response_model=ConversationsDeleteSuccessSchema,
    status_code=status.HTTP_200_OK,
    summary="Delete all conversations for the user",
    responses={
        401: {"model": APIFailureSchema, "description": "Invalid or missing access token."},
        404: {"model": APIFailureSchema, "description": "User account not found."},
        500: {"model": APIFailureSchema, "description": "Database delete operation error."}
    },
)
async def delete_conversations(
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Deletes all conversation history records belonging to the authenticated user.

    Args:
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Authenticated user payload.

    Raises:
        HTTPException: 404 Not Found if user cannot be verified.
        HTTPException: 500 Internal Server Error if mass deletion fails.

    Returns:
        ConversationsDeleteSuccessSchema: Clean confirmation signal.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account could not be found."
            )

        db.query(Conversation).filter(Conversation.user_id == user.id).delete(
            synchronize_session=False
        )
        db.commit()

        return ConversationsDeleteSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="All historical conversation data records have been successfully deleted.",
        )

    except HTTPException:
        raise
    except Exception as db_err:
        db.rollback()
        print("Mass Delete Error:", str(db_err))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error executing database clear request operations."
        )


@router.get(
    "/conversation/{conversation_id}",
    response_model=ConversationDetailsSuccessSchema,
    status_code=status.HTTP_200_OK,
    summary="Get all messages from a single conversation",
    responses={
        401: {"model": APIFailureSchema, "description": "Invalid or missing access token."},
        404: {"model": APIFailureSchema, "description": "Conversation could not be found."},
        500: {"model": APIFailureSchema, "description": "Internal database parsing error."}
    },
)
async def get_conversation(
    conversation_id: Annotated[int, Path(title="The ID of the conversation to fetch", ge=1)],
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Fetches all individual chat messages associated with a specific conversation ID.

    Args:
        conversation_id (int): Database unique primary key for the conversation.
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Authenticated user payload.

    Raises:
        HTTPException: 404 Not Found if conversation is missing or un-owned.
        HTTPException: 500 Internal Server Error if parsing message data fails.

    Returns:
        ConversationDetailsSuccessSchema: Chronological list of past messages.
    """
    try:
        # Verify conversation ownership
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

        adapter = TypeAdapter(list[MessageInfo])
        formatted_messages = adapter.dump_python(messages, mode="json")

        return ConversationDetailsSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Dialogue timeline history records loaded successfully.",
            content=formatted_messages,
        )

    except HTTPException:
        raise
    except Exception as e:
        print("Fetch Single Conversation Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data pipeline system error while extracting timeline arrays."
        )


@router.delete(
    "/conversation/{conversation_id}",
    response_model=ConversationDeleteSuccessSchema,
    status_code=status.HTTP_200_OK,
    summary="Delete a single conversation thread",
    responses={
        401: {"model": APIFailureSchema, "description": "Invalid or missing access token."},
        404: {"model": APIFailureSchema, "description": "Conversation could not be found."},
        500: {"model": APIFailureSchema, "description": "Database record delete failure."}
    },
)
async def delete_conversation(
    conversation_id: Annotated[int, Path(title="The ID of the conversation to delete", ge=1)],
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Deletes a specific conversation thread and its associated history.

    Args:
        conversation_id (int): Database unique primary key for the conversation.
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Authenticated user payload.

    Raises:
        HTTPException: 404 Not Found if target conversation is missing or un-owned.
        HTTPException: 500 Internal Server Error if database update fails.

    Returns:
        ConversationDeleteSuccessSchema: Success confirmation packet.
    """
    try:
        # Check ownership boundary before running delete commands
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

        return ConversationDeleteSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Conversation record successfully purged from database histories.",
        )

    except HTTPException:
        raise
    except Exception as db_err:
        db.rollback()
        print("Single Delete Error:", str(db_err))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction failure executing clear request command routines."
        )


@router.put(
    "/conversation/{conversation_id}",
    response_model=ConversationRenameSuccessSchema,
    status_code=status.HTTP_200_OK,
    summary="Rename a conversation title",
    responses={
        401: {"model": APIFailureSchema, "description": "Invalid or missing access token."},
        404: {"model": APIFailureSchema, "description": "Conversation could not be found."},
        500: {"model": APIFailureSchema, "description": "Database rename operation error."}
    },
)
async def rename_conversation(
    conversation_id: Annotated[int, Path(title="The ID of the conversation to rename", ge=1)],
    rename_request: ConversationRenameRequestData,
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Updates the title of a specific conversation thread belonging to the authenticated user.

    Args:
        conversation_id (int): Database unique primary key for the conversation.
        rename_request (ConversationRenameRequestData): Pydantic model containing the new title string.
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Authenticated user payload.

    Raises:
        HTTPException: 404 Not Found if requested conversation is missing or un-owned.
        HTTPException: 500 Internal Server Error if database update fails.

    Returns:
        ConversationRenameSuccessSchema: Success confirmation packet.
    """
    try:
        # Fetch conversation safely bounded by owner ID
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

        # Apply update
        conversation.title = rename_request.title
        db.commit()
        db.refresh(conversation)

        return ConversationRenameSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Conversation rename successful."
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Rename Conversation Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while updating the conversation title."
        )