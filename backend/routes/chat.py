from datetime import datetime
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..db.database import get_db
from ..models.model import Conversation, Message, User
from ..schemas.auth import AccessTokenJWTPayload
from ..schemas.base import APIFailureEnvelope
from ..schemas.chat import (
    ConversationDeleteSuccessEnvelope,
    ConversationDetailsSuccessEnvelope,
    ConversationRequest,
    ConversationsDeleteSuccessEnvelope,
    ConversationsListSuccessEnvelope,
    MessageResponseData,
    MessageSendSuccessEnvelope,
    SendMessageRequest,
)
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
            "description": "Bad Gateway: Gemini AI failed to return a response.",
        },
    },
)
async def send_message(
    message_request: SendMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Handles sending chat messages and routes them into one of three cases:
    1. Guest Chat (No user_id or conversation_id provided)
    2. Existing Chat (Both user_id and conversation_id provided)
    3. New Chat (Only user_id provided, automatically creates a new conversation)
    """
    content = message_request.message
    user_id = message_request.user_id
    conversation_id = message_request.conversation_id
    timestamp_str = str(datetime.utcnow())

    # --- GET GEMINI AI RESPONSE ---
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=content,
        )
        ai_response = response.text

        if not ai_response:
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    success=False,
                    message="The AI engine returned an empty response.",
                ).model_dump(),
            )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"AI connection failure: {str(e)}",
                # Render standard percentage/units directly if needed elsewhere
            ).model_dump(),
        )

    # --- CASE 1: GUEST CHAT (Neither ID provided) ---
    if user_id is None and conversation_id is None:
        return MessageSendSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Temporary message processed successfully",
            content=MessageResponseData(
                request=content, response=ai_response, created_at=timestamp_str
            ),
        )

    # --- CASE 2: EXISTING CONVERSATION (Both IDs provided) ---
    if conversation_id is not None and user_id is not None:
        user = db.query(User).filter(User.id == user_id).first()
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        # Validation: Verify user and conversation exist
        if not user or not conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="User or conversation thread could not be found.",
                ).model_dump(),
            )

        try:
            message = Message(
                conversation_id=int(conversation.id),
                sender=str(user.username),
                content=content,
                response=ai_response,
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
                    message=f"Database error while saving message: {str(db_err)}",
                ).model_dump(),
            )

        return MessageSendSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Message added to conversation successfully",
            content=MessageResponseData(
                request=content, response=ai_response, created_at=timestamp_str
            ),
        )

    # --- CASE 3: NEW CONVERSATION (Only user_id provided) ---
    if user_id is not None and conversation_id is None:
        user = db.query(User).filter(User.id == user_id).first()

        # Validation: Verify user exists
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="User not found. Unable to create conversation.",
                ).model_dump(),
            )

        try:
            # Create the new conversation record first
            conversation = Conversation(
                user_id=user_id,
                title=f"Chat with {user.username}",
            )
            db.add(conversation)
            db.flush()

            # Create and link the message record
            message = Message(
                conversation_id=conversation.id,
                sender=str(user.username),
                content=content,
                response=ai_response,
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
                    message=f"Database error while creating conversation: {str(db_err)}",
                ).model_dump(),
            )

        return MessageSendSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="New conversation created successfully",
            content=MessageResponseData(
                request=content, response=ai_response, created_at=timestamp_str
            ),
        )

    # --- FALLBACK: INVALID PARAMETER COMBINATIONS ---
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=APIFailureEnvelope(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message="Invalid combinations of IDs provided in request parameters.",
        ).model_dump(),
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
    # Check if the user is logged in
    if not auth_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=APIFailureEnvelope(
                status_code=status.HTTP_401_UNAUTHORIZED,
                success=False,
                message="Authentication token is missing or expired.",
            ).model_dump(),
        )

    # Check if user exists in database
    user = db.query(User).filter(User.id == auth_user.user_id).first()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIFailureEnvelope(
                status_code=status.HTTP_404_NOT_FOUND,
                success=False,
                message="User account could not be found.",
            ).model_dump(),
        )

    try:
        # Get all conversations for this user
        conversations = (
            db.query(Conversation).filter(Conversation.user_id == user.id).all()
        )

        return ConversationsListSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User conversations fetched successfully.",
            content=conversations,
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Database error while fetching conversations: {str(e)}",
            ).model_dump(),
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
            ).model_dump(),
        )

    user = db.query(User).filter(User.id == auth_user.user_id).first()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIFailureEnvelope(
                status_code=status.HTTP_404_NOT_FOUND,
                success=False,
                message="User account could not be found.",
            ).model_dump(),
        )

    try:
        # Delete conversations (Model cascades will clean up messages automatically)
        db.query(Conversation).filter(Conversation.user_id == user.id).delete(
            synchronize_session=False
        )

        # Save changes to the database
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
            ).model_dump(),
        )


@router.get(
    "/conversation",
    response_model=ConversationDetailsSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Get Messages from a Single Conversation",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Unauthorized"},
        403: {
            "model": APIFailureEnvelope,
            "description": "Forbidden: You do not access to this conversation.",
        },
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
    conversation_request: ConversationRequest = Depends(),  # Maps fields to query parameters
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
            ).model_dump(),
        )

    try:
        # Fetch the conversation record
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_request.conversation_id)
            .first()
        )

        # Validation: Verify the conversation exists
        if not conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="Conversation record could not be found.",
                ).model_dump(),
            )

        # Security: Verify ownership to block unauthorized access
        if conversation.user_id != auth_user.user_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_403_FORBIDDEN,
                    success=False,
                    message="Access Denied: You do not own this conversation.",
                ).model_dump(),
            )

        # Get all messages inside this conversation
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .all()
        )

        return ConversationDetailsSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Conversation messages loaded successfully.",
            content=messages,
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Database error while loading conversation: {str(e)}",
            ).model_dump(),
        )


@router.delete(
    "/conversation",
    response_model=ConversationDeleteSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Delete a Single Conversation",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Unauthorized"},
        403: {
            "model": APIFailureEnvelope,
            "description": "Forbidden: You are not authorized to delete this conversation.",
        },
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
    conversation_request: ConversationRequest,  # Passed inside JSON Body payload
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
            ).model_dump(),
        )

    try:
        # Locate the conversation record
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_request.conversation_id)
            .first()
        )

        # Validation: Verify it exists
        if not conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="Conversation not found.",
                ).model_dump(),
            )

        # Security: Verify ownership before deleting
        if conversation.user_id != auth_user.user_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_403_FORBIDDEN,
                    success=False,
                    message="Access Denied: You are not authorized to delete this conversation.",
                ).model_dump(),
            )

        # Delete conversation (Cascades clean up messages automatically)
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
            ).model_dump(),
        )