from sqlalchemy.orm import Session
from ..models.model import User
from ..schemas.token_schema import Token
from ..schemas.user_schema import GetUser, SigninSchema
from ..utils.auth_utils import (
    verify_password,
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
    hash_token, get_current_user
)
from ..db.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signin", response_model=Token)
async def login_user(
    user_credential: SigninSchema ,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == user_credential.username).first()

    if not user or not verify_password(user_credential.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials."
        )

    #Create the raw tokens to send to the client
    access_token = create_access_token({"user_id": user.id, "username": user.username})
    refresh_token = create_refresh_token(user_id=user.id)

    # Store HASHED versions in the database
    user.access_token = hash_token(access_token)
    user.refresh_token = hash_token(refresh_token)
    db.commit()

    # Return the RAW tokens to the user (they store this in local storage/cookies)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="Bearer")


@router.post("/refresh", response_model=Token)
async def token_refresh(
        refresh_token: str,
        db: Session = Depends(get_db)
):

    user_id: int = await validate_refresh_token(refresh_token)
    hashed_incoming_refresh = hash_token(refresh_token)
    user = db.query(User).filter(User.id == user_id).first()

    # Check if the user exists and if the hashed token matches what we have on file
    if not user or user.refresh_token != hashed_incoming_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token."
        )

    new_access_token = create_access_token({"user_id": user.id, "username": user.username})

    user.access_token = hash_token(new_access_token)
    db.commit()

    return Token(access_token=new_access_token, refresh_token=refresh_token, token_type="Bearer")


@router.post("/logout")
async def logout_user(
        db: Session = Depends(get_db),
        # This automatically gives us the raw token string from the Authorization header
        authenticated_user: GetUser = Depends(get_current_user)
):

    user = db.query(User).filter(User.id == authenticated_user.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    # Wipe them out
    user.access_token = None
    user.refresh_token = None
    db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "message": "Successfully logged out."
    }