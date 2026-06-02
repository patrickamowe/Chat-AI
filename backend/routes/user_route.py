from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.model import User
from ..schemas.user_schema import UserSchema, UserResponse, GetUser
from ..utils.auth_utils import get_password_hash, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/sign-up", response_model=UserResponse)
async def create_user(user: UserSchema, db: Session = Depends(get_db)):
    """create new user object"""

    #Check the database if user with the username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Store User detail in the db
    new_user = User(
        username=user.username,
        password=get_password_hash(user.password),
        email=user.email,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
        user_id: int,
        db: Session = Depends(get_db),
        authenticated_user: GetUser = Depends(get_current_user)
):
    """Fetch and return user object by user id."""

    if authenticated_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to view this resource."
        )


    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return user
