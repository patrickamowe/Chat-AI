from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.model import User
from ..schemas.auth import (
    AccessTokenJWTPayload,
    AuthenticatedUserFields,
    LoginResponseData,
    RefreshTokenJWTPayload,
    TokenRefreshRequestData,
    TokenRefreshResponseData,
    TokenValidationRequestData,
    UserLoginRequestData,
    UserLoginSuccessSchema,
    UserLogoutSuccessSchema,
    TokenRefreshSuccessSchema,
    ValidAccessTokenResponseData,
    ValidAccessTokenSuccessSchema,
)
from ..schemas.base import APIFailureSchema
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
    response_model=UserLoginSuccessSchema,
    summary="Log in a user",
    responses={
        400: {"model": APIFailureSchema, "description": "Invalid username or password."},
        500: {"model": APIFailureSchema, "description": "Internal server error."}
    }
)
async def login_user(
    user_credential: UserLoginRequestData,
    db: Session = Depends(get_db)
):
    """
    Verifies user credentials and logs the user into the system.

    Validates the username and password. If correct, generates a new pair
    of access and refresh tokens, hashes them for secure storage, and returns them.

    Args:
        user_credential (UserLoginRequestData): The username and password payload.
        db (Session): Database session dependency.

    Raises:
        HTTPException: 400 Bad Request if the credentials do not match.
        HTTPException: 500 Internal Server Error if a database or server fault occurs.

    Returns:
        UserLoginSuccessSchema: Payload with access/refresh tokens and user details.
    """
    try:
        user = db.query(User).filter(User.username == user_credential.username.lower()).first()

        if not user or not verify_password(user_credential.password, str(user.password)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username or password. Please try again."
            )

        # Generate fresh tokens
        access_token = create_access_token({"user_id": user.id, "username": user.username})
        refresh_token = create_refresh_token(user_id=int(user.id))

        # Hash and save token records to track active sessions
        user.access_token = hash_token(access_token)
        user.refresh_token = hash_token(refresh_token)
        db.commit()

        return UserLoginSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Sign-in successful! Welcome back.",
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
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Login Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during sign-in."
        )


@router.post(
    "/refresh",
    response_model=TokenRefreshSuccessSchema,
    summary="Renew an expired access token",
    responses={
        401: {"model": APIFailureSchema, "description": "Invalid, expired, or revoked token status."},
        500: {"model": APIFailureSchema, "description": "Internal server error."}
    }
)
async def token_refresh(
    token: TokenRefreshRequestData,
    db: Session = Depends(get_db)
):
    """
    Exchanges a valid refresh token for a new access token.

    Decodes the incoming refresh token to confirm its validity and checks it
    against the stored hash in the database. If it matches, a new access token is generated.

    Args:
        token (TokenRefreshRequestData): Payload containing the refresh token string.
        db (Session): Database session dependency.

    Raises:
        HTTPException: 401 Unauthorized if token validation fails or the session was revoked.
        HTTPException: 500 Internal Server Error if database saving fails.

    Returns:
        TokenRefreshSuccessSchema: Response containing the newly generated access token.
    """
    try:
        # Verify the refresh token structure and expiration status
        try:
            payload: RefreshTokenJWTPayload = validate_refresh_token(token=token.refresh_token)
            user_id: int = payload.user_id
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The provided refresh token is invalid or has expired."
            )

        user = db.query(User).filter(User.id == user_id).first()

        # Ensure the token matches the hashed record stored in the database
        if not user or user.refresh_token != hash_token(token.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This authentication session has been revoked or modified."
            )

        # Issue a new access token
        new_access_token = create_access_token({"user_id": user.id, "username": user.username})
        user.access_token = hash_token(new_access_token)
        db.commit()

        return TokenRefreshSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Access token renewed successfully.",
            content=TokenRefreshResponseData(
                access_token=new_access_token,
                refresh_token=token.refresh_token
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Token Refresh Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during token renewal."
        )


@router.post(
    "/validate",
    response_model=ValidAccessTokenSuccessSchema,
    summary="Validate an access token",
    responses={
        401: {"model": APIFailureSchema, "description": "Token is dead, malformed, or compromised."},
        500: {"model": APIFailureSchema, "description": "Internal server error."}
    }
)
async def validate_token(
    token: TokenValidationRequestData,
    db: Session = Depends(get_db)
):
    """
    Checks if an access token is valid and active.

    Decodes the token signature and verifies it matches the active database token record
    to ensure it has not been invalidated by a logout event.

    Args:
        token (TokenValidationRequestData): Payload containing the access token string.
        db (Session): Database session dependency.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid, expired, or revoked.
        HTTPException: 500 Internal Server Error if an unexpected parsing error occurs.

    Returns:
        ValidAccessTokenSuccessSchema: Verification confirmation along with user metadata.
    """
    try:
        try:
            payload: AccessTokenJWTPayload = validate_access_token(token=token.access_token)
            user_id = payload.user_id
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token is invalid or has expired."
            )

        user = db.query(User).filter(User.id == user_id).first()

        if not user or user.access_token != hash_token(token.access_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token session has been explicitly revoked or overwritten."
            )

        return ValidAccessTokenSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Access token is verified and valid.",
            content=ValidAccessTokenResponseData(
                valid=True,
                user=AuthenticatedUserFields(
                    id=int(user.id),
                    username=str(user.username),
                    email=str(user.email)
                )
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        print("Token Validation Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during token validation."
        )


@router.post(
    "/logout",
    response_model=UserLogoutSuccessSchema,
    summary="Log out the current user",
    responses={
        401: {"model": APIFailureSchema, "description": "Invalid or missing access token."},
        404: {"model": APIFailureSchema, "description": "User profile not found."},
        500: {"model": APIFailureSchema, "description": "Internal server error."}
    }
)
async def logout_user(
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user)
):
    """
    Logs out the user and invalidates their current session tokens.

    Clears both the saved access and refresh token values inside the user's
    database record so they can no longer be used.

    Args:
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded payload from the active access token.

    Raises:
        HTTPException: 404 Not Found if the user record cannot be located.
        HTTPException: 500 Internal Server Error if database update operations fail.

    Returns:
        UserLogoutSuccessSchema: Success confirmation payload.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested user session could not be found."
            )

        # Invalidate active keys inside the database record
        user.access_token = None
        user.refresh_token = None
        db.commit()

        return UserLogoutSuccessSchema(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Successfully logged out.",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Logout Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during logout procedures."
        )