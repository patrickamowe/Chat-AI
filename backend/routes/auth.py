from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..db.database import get_db
from ..models.model import User
from ..schemas.auth import (
    AccessTokenJWTPayload,
    AuthenticatedUserFields,
    LoginResponseData,
    RefreshTokenJWTPayload,
    TokenRefreshRequest,
    TokenRefreshResponseData,
    TokenValidationRequest,
    UserLoginRequest,
    UserLoginSuccessEnvelope,
    UserLogoutSuccessEnvelope,
    TokenRefreshSuccessEnvelope,
    ValidAccessTokenResponseData,
    ValidAccessTokenSuccessEnvelope,
)
from ..schemas.base import APIFailureEnvelope
from ..utils.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_token,
    validate_access_token,
    validate_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signin",
    response_model=UserLoginSuccessEnvelope,
    summary="User Login",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid username or password."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def login_user(
    user_credential: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Logs in a user by verifying their password.

    If successful, generates and saves new tokens to the database,
    then returns them alongside the user's profile info.
    """
    try:
        user = db.query(User).filter(User.username == user_credential.username).first()

        # Check if user exists and password matches
        if not user or not verify_password(user_credential.password, str(user.password)):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    message="Invalid username or password."
                ).model_dump()
            )

        # Generate tokens
        access_token = create_access_token({"user_id": user.id, "username": user.username})
        refresh_token = create_refresh_token(user_id=int(user.id))

        # Hash and save tokens to the database
        user.access_token = hash_token(access_token)
        user.refresh_token = hash_token(refresh_token)
        db.commit()

        return UserLoginSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Sign-in successful!",
            content=LoginResponseData(
                access_token=access_token,
                refresh_token=refresh_token,
                user=AuthenticatedUserFields(
                    id=int(user.id),
                    username=str(user.username),
                    email=str(user.email)
                )
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Internal server error: {str(e)}"
            ).model_dump()
        )


@router.post(
    "/refresh",
    response_model=TokenRefreshSuccessEnvelope,
    summary="Refresh Access Token",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or expired refresh token."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def token_refresh(token: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    Swaps a refresh token for a new access token.

    The frontend runs this in the background when the access token expires
    so the user stays logged in seamlessly.
    """
    try:
        # Verify the refresh token structure and expiration
        try:
            payload: RefreshTokenJWTPayload = await validate_refresh_token(token=token.refresh_token)
            user_id: int = payload.user_id
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    message="Refresh token is invalid or expired."
                ).model_dump()
            )

        user = db.query(User).filter(User.id == user_id).first()

        # Check if user exists and match the stored token hash
        if not user or user.refresh_token != hash_token(token.refresh_token):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    message="Token session has been revoked or modified."
                ).model_dump()
            )

        # Issue new access token
        new_access_token = create_access_token({"user_id": user.id, "username": user.username})
        user.access_token = hash_token(new_access_token)
        db.commit()

        return TokenRefreshSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Access token renewed successfully.",
            content=TokenRefreshResponseData(
                access_token=new_access_token,
                refresh_token=token.refresh_token
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Internal server error: {str(e)}"
            ).model_dump()
        )


@router.post(
    "/validate",
    response_model=ValidAccessTokenSuccessEnvelope,
    summary="Validate Access Token",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or expired access token."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def validate_token(
    token: TokenValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Checks if an access token is valid.

    The frontend uses this route to confirm a user is still authenticated
    before loading private routes or components.
    """
    try:
        # Verify the access token structure and expiration
        try:
            payload: AccessTokenJWTPayload = await validate_access_token(token=token.access_token)
            user_id = payload.user_id
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    message="Access token is invalid or expired."
                ).model_dump()
            )

        user = db.query(User).filter(User.id == user_id).first()

        # Check if user exists and match the stored token hash
        if not user or user.access_token != hash_token(token.access_token):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    message="Token session has been revoked or modified."
                ).model_dump()
            )

        return ValidAccessTokenSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Access token is valid.",
            content=ValidAccessTokenResponseData(
                valid=True,
                user=AuthenticatedUserFields(
                    id=int(user.id),
                    username=str(user.username),
                    email=str(user.email)
                )
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Internal server error: {str(e)}"
            ).model_dump()
        )


@router.post(
    "/logout",
    response_model=UserLogoutSuccessEnvelope,
    summary="User Logout",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Missing or invalid access token."},
        404: {"model": APIFailureEnvelope, "description": "User account not found."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def logout_user(
    db: Session = Depends(get_db),
    auth_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user)
):
    """
    Logs out the user and clears their active session tokens from the database.
    """
    try:
        # Check if user is authenticated
        if not auth_user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    message="Invalid or expired access token."
                ).model_dump()
            )

        user = db.query(User).filter(User.id == auth_user.user_id).first()

        # Check if user exists in database
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    message="User profile not found."
                ).model_dump()
            )

        # Invalidate tokens by clearing them from the database
        user.access_token = None
        user.refresh_token = None
        db.commit()

        return UserLogoutSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Successfully logged out.",
            content=None
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message=f"Internal server error: {str(e)}"
            ).model_dump()
        )