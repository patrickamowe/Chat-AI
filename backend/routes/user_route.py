# app/routers/users.py
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..db.database import get_db
from ..models.model import User

# Import your clean, descriptive schemas
from ..schemas.request_schemas import AccessTokenJWTPayload, UserRegistrationRequest
from ..schemas.response_schemas import (
    UserRegistrationSuccessEnvelope,
    UserProfileFetchSuccessEnvelope,
    APIFailureEnvelope,
    UserProfileResponseData
)
from ..utils.auth_utils import get_password_hash, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/signup",
    response_model=UserRegistrationSuccessEnvelope,
    responses={
        400: {"model": APIFailureEnvelope, "description": "Username already taken"},
        500: {"model": APIFailureEnvelope, "description": "Database or server failure"}
    }
)
async def create_user(
        user_data: UserRegistrationRequest,
        db: Session = Depends(get_db)
):
    """
    Registers a brand-new user account in our system.

    It checks if the username is already taken, hashes the plain-text password 
    safely, and saves the new profile record to the database.
    """
    try:
        # Check the database if user with the username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    success=False,
                    message="Username is already taken. Please choose another one."
                ).model_dump()
            )

        # Hash password and store user details in the DB
        new_user = User(
            username=user_data.username,
            password=get_password_hash(user_data.password),
            email=user_data.email,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return UserRegistrationSuccessEnvelope(
            status_code=status.HTTP_201_CREATED,
            success=True,
            message="User account created successfully!",
            content=UserProfileResponseData.model_validate(new_user)
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Internal server error while creating account: {str(e)}"
            ).model_dump()
        )


@router.get(
    "/{user_id}",
    response_model=UserProfileFetchSuccessEnvelope,
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid, expired, or missing access token"},
        403: {"model": APIFailureEnvelope, "description": "User attempting to spy on another profile"},
        404: {"model": APIFailureEnvelope, "description": "Target profile does not exist"},
        500: {"model": APIFailureEnvelope, "description": "Server or database crash"}
    }
)
async def get_user(
        user_id: int,
        db: Session = Depends(get_db),
        authenticated_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user)
):
    """
    Retrieves a single user's profile details using their Unique ID.

    This endpoint is protected; users are blocked from looking up profiles 
    that do not belong to them.
    """
    try:
        # 401 Error: Frontend didn't pass a valid logged-in token
        if not authenticated_user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    message="You must be logged in to access this profile."
                ).model_dump()
            )

        # 403 Error: Token is valid, but user_id in token doesn't match the URL path request
        if authenticated_user.user_id != user_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_403_FORBIDDEN,
                    success=False,
                    message="Access denied. You do not have permission to view other users' profiles."
                ).model_dump()
            )

        user = db.query(User).filter(User.id == user_id).first()

        # 404 Error: Account doesn't exist in the system anymore
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="The requested user profile could not be found."
                ).model_dump()
            )

        return UserProfileFetchSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User profile retrieved successfully.",
            content=UserProfileResponseData.model_validate(user)
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Internal server error during profile lookup: {str(e)}"
            ).model_dump()
        )