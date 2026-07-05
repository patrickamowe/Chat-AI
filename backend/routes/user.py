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

    Checks if the username is unique, hashes the password,
    and saves the new user record to the database.

    Args:
        user_data (UserRegistrationRequest): The registration details (username, email, password).
        db (Session): Database session dependency.

    Raises:
        HTTPException: 400 Bad Request if the username is already taken.
        HTTPException: 500 Internal Server Error if the database save operation fails.

    Returns:
        UserRegistrationSuccessEnvelope: The profile details of the newly created user.
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
        print("User Signup Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating your account."
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
    Fetches the profile details of the currently logged-in user.

    Uses the user ID from the active JWT token to lookup and return account details.

    Args:
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT token payload.

    Raises:
        HTTPException: 404 Not Found if the user ID does not match any database record.
        HTTPException: 500 Internal Server Error if the database query fails.

    Returns:
        UserProfileFetchSuccessEnvelope: Object containing the user's account profile details.
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
        print("Fetch Profile Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching your profile details."
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
    Permanently deletes a user account from the system.

    Finds the user record, prepares their metadata for the final confirmation message,
    and removes the record from the database.

    Args:
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT token payload.

    Raises:
        HTTPException: 404 Not Found if the user profile cannot be located.
        HTTPException: 500 Internal Server Error if the database delete operation fails.

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

        # Map data into Pydantic before deletion to avoid session lazy-loading errors post-commit
        deleted_user_data = UserProfileResponseData.model_validate(user)

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
        print("Delete Profile Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting your profile account."
        )


@router.put(
    "/profile",
    response_model=UserProfileEditSuccessEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Update user profile details",
    responses={
        400: {"model": APIFailureEnvelope, "description": "The username already exists."},
        401: {"model": APIFailureEnvelope, "description": "Invalid or missing access token."},
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
    Updates basic contact information (username and email) for the logged-in user.

    Args:
        user_details (UserEditDetailsRequest): The updated username and email fields.
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT token payload.

    Raises:
        HTTPException: 400 Bad Request if the new username is already taken by someone else.
        HTTPException: 404 Not Found if the user profile cannot be found.
        HTTPException: 500 Internal Server Error if database saving fails.

    Returns:
        UserProfileEditSuccessEnvelope: Confirmation indicating a successful profile update.
    """
    try:
        user = db.query(User).filter(User.id == auth_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested user profile could not be found."
            )

        # Ensure the target new username isn't stolen by another account
        username_existed = db.query(User).filter(User.username == user_details.username.lower()).first()
        if username_existed and username_existed.id != user.id:
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
        print("Edit Profile Details Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while updating your profile details."
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

    Validates the current password before hashing and saving the new credentials choice.

    Args:
        user_passwords (UserEditPasswordRequest): Payload containing both the old and new passwords.
        db (Session): Database session dependency.
        auth_user (AccessTokenJWTPayload): Decoded JWT token payload.

    Raises:
        HTTPException: 400 Bad Request if the current password check fails.
        HTTPException: 404 Not Found if the target user profile doesn't exist.
        HTTPException: 500 Internal Server Error if security hashing or database commits fail.

    Returns:
        UserProfileEditSuccessEnvelope: Confirmation of a successful password change.
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
        print("Edit Password Error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while applying your new password."
        )