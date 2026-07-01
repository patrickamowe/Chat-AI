from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.model import User
from ..schemas.auth import (
    AccessTokenJWTPayload,
    UserProfileFetchSuccessEnvelope,
    UserProfileResponseData,
    UserProfileEditSuccessEnvelope,
    UserRegistrationRequest,
    UserEditPasswordRequest,
    UserEditDetailsRequest,
    UserRegistrationSuccessEnvelope
)
from ..schemas.base import APIFailureEnvelope
from ..utils.auth import get_current_user, get_password_hash, verify_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/signup",
    response_model=UserRegistrationSuccessEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    responses={
        400: {"model": APIFailureEnvelope, "description": "Registration failed due to client error."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def create_user(
        user_data: UserRegistrationRequest,
        db: Session = Depends(get_db)
):
    """
    Registers a new user within the system.

    This endpoint verifies the uniqueness of the provided username, hashes
    the plaintext password using a secure hashing algorithm, and persists
    the new user record to the database.

    Args:
        user_data (UserRegistrationRequest): The incoming user profile and credential data.
        db (Session): The SQLAlchemy database session dependency.

    Raises:
        HTTPException: 400 Bad Request if the username is already registered.
        HTTPException: 500 Internal Server Error for unhandled database exceptions.

    Returns:
        UserRegistrationSuccessEnvelope: The newly created user profile details.
    """
    try:
        # Check if the username is already taken
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken. Please choose another one."
            )

        # Hash the password and save the new user
        new_user = User(
            username=user_data.username.lower(),
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

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while creating your account: {str(e)}"
        )


@router.get(
    "/profile",
    response_model=UserProfileFetchSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current user profile",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "User profile not found."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def get_user_info(
        db: Session = Depends(get_db),
        auth_user: AccessTokenJWTPayload = Depends(get_current_user)
):
    """
    Fetches the profile details of the currently authenticated user.

    Utilizes the JWT token payload extracted from the authorization header
    to locate and return the user's account details.

    Args:
        db (Session): The SQLAlchemy database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT token details for the current user.

    Raises:
        HTTPException: 404 Not Found if the user ID from the token does not exist.
        HTTPException: 500 Internal Server Error for unhandled system exceptions.

    Returns:
        UserProfileFetchSuccessEnvelope: Object containing user account details.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested user profile could not be found."
            )

        return UserProfileFetchSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User profile retrieved successfully.",
            content=UserProfileResponseData.model_validate(user)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the profile: {str(e)}"
        )

@router.delete(
    "/profile",
    response_model=UserProfileFetchSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Permanently delete user profile",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "User profile not found."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def delete_profile(
    db: Session = Depends(get_db),
    auth_user: AccessTokenJWTPayload = Depends(get_current_user)
):
    """
    Permanently purges a user's account and profile from the system.

    Locates the user record corresponding to the authenticated user ID,
    serializes their profile metadata for the final response envelope,
    and removes the record entirely from the persistent database.

    Args:
        db (Session): The SQLAlchemy database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT token payload of the currently authenticated user.

    Raises:
        HTTPException: 404 Not Found if the user ID from the token cannot be found in the database.
        HTTPException: 500 Internal Server Error for unhandled database exceptions during deletion.

    Returns:
        UserProfileFetchSuccessEnvelope: The profile data of the deleted user account.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested user profile could not be found."
            )

        # Map the profile data into Pydantic BEFORE deleting the DB record
        # to avoid Access/Session serialization errors post-commit.
        deleted_user_data = UserProfileResponseData.model_validate(user)

        # Safely delete the user instance using the database session
        db.delete(user)
        db.commit()

        return UserProfileFetchSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Your user profile and account details have been permanently deleted.",
            content=deleted_user_data
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while deleting your profile: {str(e)}"
        )
@router.put(
    "/profile",
    response_model=UserProfileEditSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Update user profile details",
    responses={
        401: {"model": APIFailureEnvelope, "description": "The username already exist, Invalid or missing access token."},
        404: {"model": APIFailureEnvelope, "description": "User profile not found."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def edit_profile(
        user_details: UserEditDetailsRequest,
        db: Session = Depends(get_db),
        auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Updates the contact information (username and email) for the authenticated user.

    Args:
        user_details (UserEditDetailsRequest): The modified profile parameters.
        db (Session): The SQLAlchemy database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT token details for the current user.

    Raises:
        HTTPException: 401 The username is taken.
        HTTPException: 404 Not Found if the user session points to a non-existent record.
        HTTPException: 500 Internal Server Error on database synchronization failures.

    Returns:
        UserProfileFetchSuccessEnvelope: The updated user profile data.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested user profile could not be found."
            )

        username_existed = db.query(User).filter(User.username == user_details.username.lower()).first()
        if username_existed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken by another user."
            )

        user.username = user_details.username.lower()
        user.email = user_details.email
        db.commit()
        db.refresh(user)

        return UserProfileEditSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User profile details updated successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating profile details: {str(e)}"
        )


@router.put(
    "/password",
    response_model=UserProfileEditSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Update user password",
    responses={
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
        400: {"model": APIFailureEnvelope, "description": "Incorrect current password provided."},
        404: {"model": APIFailureEnvelope, "description": "User profile not found."},
        500: {"model": APIFailureEnvelope, "description": "Internal server error."}
    }
)
async def edit_password(
        user_passwords: UserEditPasswordRequest,
        db: Session = Depends(get_db),
        auth_user: AccessTokenJWTPayload = Depends(get_current_user),
):
    """
    Changes the password for the currently logged-in user.

    Verifies the user's existing password before allowing them to apply
    and hash a brand-new credentials choice.

    Args:
        user_passwords (UserEditPasswordRequest): Payload containing old and new passwords.
        db (Session): The SQLAlchemy database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT token details for the current user.

    Raises:
        HTTPException: 400 Bad Request if the current password check fails.
        HTTPException: 404 Not Found if the target user profile doesn't exist.
        HTTPException: 500 Internal Server Error for processing/hashing failures.

    Returns:
        UserProfileFetchSuccessEnvelope: Confirmation of successful password modification.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested user profile could not be found."
            )

        if not verify_password(user_passwords.password, str(user.password)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The current password you provided is incorrect."
            )

        user.password = get_password_hash(user_passwords.new_password)
        db.commit()
        db.refresh(user)

        return UserProfileEditSuccessEnvelope(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Your password has been changed successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while changing your password: {str(e)}"
        )