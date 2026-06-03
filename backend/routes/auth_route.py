# app/routers/auth.py
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..db.database import get_db
from ..models.model import User

# Importing the newly named, highly descriptive schemas
from ..schemas.request_schemas import UserLoginRequest, AccessTokenJWTPayload
from ..schemas.response_schemas import (
    UserLoginSuccessEnvelope,
    TokenRefreshSuccessEnvelope,
    UserLogoutSuccessEnvelope,
    APIFailureEnvelope,
    LoginResponseData,
    AuthenticatedUserFields,
    TokenRefreshResponseData
)
from ..utils.auth_utils import (
    verify_password, create_access_token, create_refresh_token,
    validate_refresh_token, hash_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signin",
    response_model=UserLoginSuccessEnvelope,
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid login credentials"},
        500: {"model": APIFailureEnvelope, "description": "Server or database crash"}
    }
)
async def login_user(
        user_credential: UserLoginRequest,
        db: Session = Depends(get_db)
):
    """
    Logs a user into the system by verifying their password.

    If successful, it updates their tokens in the database and returns a fresh
    pair of JWT tokens along with basic user profile information.
    """
    try:
        user = db.query(User).filter(User.username == user_credential.username).first()

        # 401 Credential Error
        if not user or not verify_password(user_credential.password, user.password):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=401,
                    success=False,
                    message="Invalid username or password."
                ).model_dump()
            )

        access_token = create_access_token({"user_id": user.id, "username": user.username})
        refresh_token = create_refresh_token(user_id=user.id)

        user.access_token = hash_token(access_token)
        user.refresh_token = hash_token(refresh_token)
        db.commit()

        return UserLoginSuccessEnvelope(
            status_code=200,
            success=True,
            message="Sign-in successful!",
            content=LoginResponseData(
                access_token=access_token,
                refresh_token=refresh_token,
                user=AuthenticatedUserFields(
                    id=user.id,
                    username=user.username,
                    email=user.email
                )
            )
        )
    except Exception as e:
        # 500 Catch-All Server/Database Error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=500,
                success=False,
                message=f"Internal server error: {str(e)}"
            ).model_dump()
        )


@router.post(
    "/refresh",
    response_model=TokenRefreshSuccessEnvelope,
    responses={
        401: {"model": APIFailureEnvelope, "description": "Expired or altered refresh token"},
        500: {"model": APIFailureEnvelope, "description": "Server or database crash"}
    }
)
async def token_refresh(refresh_token: str, db: Session = Depends(get_db)):
    """
    Swaps a long-lived refresh token for a brand-new access token.

    This is run quietly by the frontend when an access token expires so the
    user doesn't get kicked out of their active dashboard session.
    """
    try:
        # Validates token parsing natively
        try:
            user_id: int = await validate_refresh_token(refresh_token)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=401,
                    success=False,
                    message="Refresh token is invalid or expired."
                ).model_dump()
            )

        user = db.query(User).filter(User.id == user_id).first()

        # 401 Session Mismatch / Revoked Token Error
        if not user or user.refresh_token != hash_token(refresh_token):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=401,
                    success=False,
                    message="Token session has been revoked or modified."
                ).model_dump()
            )

        new_access_token = create_access_token({"user_id": user.id, "username": user.username})
        user.access_token = hash_token(new_access_token)
        db.commit()

        return TokenRefreshSuccessEnvelope(
            status_code=200,
            success=True,
            message="Access token renewed successfully.",
            content=TokenRefreshResponseData(
                access_token=new_access_token,
                refresh_token=refresh_token
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=500,
                success=False,
                message=f"Internal server error: {str(e)}"
            ).model_dump()
        )


@router.post(
    "/logout",
    response_model=UserLogoutSuccessEnvelope,
    responses={
        401: {"model": APIFailureEnvelope, "description": "Missing or invalid access token"},
        404: {"model": APIFailureEnvelope, "description": "User session not found"},
        500: {"model": APIFailureEnvelope, "description": "Server or database crash"}
    }
)
async def logout_user(
        db: Session = Depends(get_db),
        authenticated_user: Optional[AccessTokenJWTPayload] = Depends(get_current_user)
):
    """
    Logs the user out and clears their active token session from the database.

    This instantly invalidates both their access and refresh tokens across the app.
    """
    try:
        # 401 Invalid/Missing Token Error managed cleanly in the route
        if not authenticated_user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIFailureEnvelope(
                    status_code=401,
                    success=False,
                    message="Invalid or expired access token."
                ).model_dump()
            )

        user = db.query(User).filter(User.id == authenticated_user.user_id).first()

        # 404 Missing Session Error
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIFailureEnvelope(
                    status_code=404,
                    success=False,
                    message="Active user profile session not found."
                ).model_dump()
            )

        # Clear tracking tokens to invalidate the session entirely
        user.access_token = None
        user.refresh_token = None
        db.commit()

        return UserLogoutSuccessEnvelope(
            status_code=200,
            success=True,
            message="Successfully logged out.",
            content=None
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIFailureEnvelope(
                status_code=500,
                success=False,
                message=f"Internal server error: {str(e)}"
            ).model_dump()
        )