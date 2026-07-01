from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

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
    summary="Authenticate user credentials",
    responses={
        400: {"model": APIFailureEnvelope, "description": "Invalid username or password."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def login_user(
    user_credential: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Verifies user credentials and establishes an authenticated session.

    Validates the provided username and password. Upon successful validation,
    generates a stateful matching pair of access and refresh tokens, hashes
    them for secure database validation/revocation, and returns them with user information.

    Args:
        user_credential (UserLoginRequest): Username and password login payload.
        db (Session): The SQLAlchemy database session dependency.

    Raises:
        HTTPException: 400 Bad Request if authentication matching fails.
        HTTPException: 500 Internal Server Error on unexpected systemic faults.

    Returns:
        UserLoginSuccessEnvelope: Payload with access/refresh tokens and user meta fields.
    """
    try:
        user = db.query(User).filter(User.username == user_credential.username.lower()).first()

        if not user or not verify_password(user_credential.password, str(user.password)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username or password. Please try again."
            )

        # Generate tokens
        access_token = create_access_token({"user_id": user.id, "username": user.username})
        refresh_token = create_refresh_token(user_id=int(user.id))

        # Hash and save tokens to the database tracking session status
        user.access_token = hash_token(access_token)
        user.refresh_token = hash_token(refresh_token)
        db.commit()

        return UserLoginSuccessEnvelope(
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during sign-in: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenRefreshSuccessEnvelope,
    summary="Renew expired access tokens",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid, expired, or revoked token status."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def token_refresh(
    token: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Swaps a valid refresh token for a newly issued short-lived access token.

    Decodes the incoming refresh token to ensure validity and checks it against
    the active hash stored in the database. If matched, regenerates a clean access token.

    Args:
        token (TokenRefreshRequest): Input model containing the active refresh token.
        db (Session): The SQLAlchemy database session dependency.

    Raises:
        HTTPException: 401 Unauthorized if token validation fails or session is revoked.
        HTTPException: 500 Internal Server Error on processing exceptions.

    Returns:
        TokenRefreshSuccessEnvelope: Response containing a newly populated access token.
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

        # Enforce exact structural match against hashed database instance tracking
        if not user or user.refresh_token != hash_token(token.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This authentication session has been revoked or modified."
            )

        # Issue fresh access token mapping
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
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during token renewal: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=ValidAccessTokenSuccessEnvelope,
    summary="Validate an access token",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Token is dead, malformed, or compromised."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def validate_token(
    token: TokenValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Confirms client authentication status by auditing an active access token.

    Decodes signature metadata and coordinates against the persistent token storage hashes
    to assure the token has not been prematurely dropped by a logging event.

    Args:
        token (TokenValidationRequest): Payload containing the target access token.
        db (Session): The SQLAlchemy database session dependency.

    Raises:
        HTTPException: 401 Unauthorized if signature verification fails or token is revoked.
        HTTPException: 500 Internal Server Error on processing exceptions.

    Returns:
        ValidAccessTokenSuccessEnvelope: Verification packet affirming authentication state.
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

        return ValidAccessTokenSuccessEnvelope(
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during token validation: {str(e)}"
        )


@router.post(
    "/logout",
    response_model=UserLogoutSuccessEnvelope,
    summary="Terminate active session",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "Associated record targets missing."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def logout_user(
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user)
):
    """
    Invalidates current access parameters and destroys stored backend token tracking hashes.

    Acts as an explicit security fence by nullifying access and refresh validation matrices
    tied directly to the processing user profile identifier.

    Args:
        db (Session): The SQLAlchemy database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT context payload passed from depend handlers.

    Raises:
        HTTPException: 404 Not Found if authentication identity context holds no valid record.
        HTTPException: 500 Internal Server Error on persistence state adjustment issues.

    Returns:
        UserLogoutSuccessEnvelope: Clean termination validation payload.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested user session could not be found."
            )

        # Invalidate active keys inside the database
        user.access_token = None
        user.refresh_token = None
        db.commit()

        return UserLogoutSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Successfully logged out. Your session keys have been cleared.",
            content=None
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during logout procedures: {str(e)}"
        )