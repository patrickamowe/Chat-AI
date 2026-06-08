# app/routers/users.py
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..db.database import get_db
from ..models.model import User
from ..schemas.auth import (
    AccessTokenJWTPayload,
    UserProfileFetchSuccessEnvelope,
    UserProfileResponseData,
    UserRegistrationRequest,
    UserRegistrationSuccessEnvelope,
)
from ..schemas.base import APIFailureEnvelope
from ..utils.auth import get_current_user, get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/signup",
    response_model=UserRegistrationSuccessEnvelope,
    summary="User Registration",
    responses={
        400: {"model": APIFailureEnvelope, "description": "Username already taken."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def create_user(
    user_data: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Registers a new user account.
    Checks if the username is unique, hashes the password, and saves the user record.
    """
    try:
        # Check if the username is already taken
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

        # Hash the password and save the new user
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
    "/profile",
    response_model=UserProfileFetchSuccessEnvelope,
    summary="Get User Profile",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "User profile not found."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def get_user_info(
    db: Session = Depends(get_db),
    auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user)
):
    """
    Retrieves the profile details of the currently logged-in user.
    """
    try:
        # Check if the user is authenticated
        if not auth_user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    message="You must be logged in to access this profile."
                ).model_dump()
            )

        user = db.query(User).filter(User.id == auth_user.user_id).first()

        # Check if the user exists in the database
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