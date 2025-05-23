from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from ..utils.auth import (hash_password,
                          authenticate_user,
                          create_access_token,
                          get_current_active_user)
from ..database.db import get_db
from ..database.models import User

from ..data_models import user as user_dm

from typing import Annotated
from datetime import timedelta

router = APIRouter()

@router.get("/request")
async def status():
    return {"message": "Auth router is working!"}

@router.post("/signup", response_model=user_dm.User)
async def user_signup(username: str, password: str, email: str, db: Annotated[Session, Depends(get_db)]):
    """
    Standard user sign up. Both username and email must unique.

    - **username**: Username.
    - **password**: Password.
    - **email**: Email.
    """

    username_check = db.query(User).filter(User.username == username or User.email == email).first()
    if username_check:
        raise HTTPException(
            status_code=401,
            detail="Username/email is already taken. Use a different one."
        )
    new_user = User(username=username, email=email, hashed_password=hash_password(password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user



@router.post("/token", tags=["authorization"])
def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[Session, Depends(get_db)]
    ):
    """
    Request a new token providing user data.

    - **form_data**: Authorization form data.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={'WWW-Authenticate': "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    scopes = []
    if user.role == User.RoleEnum.admin:
        scopes = ["admin"]
    access_token = create_access_token(
        data={"sub": user.username, "scopes": scopes},
        expires_delta=access_token_expires
        )
    return {"access_token": access_token, "token_type":"bearer"}

@router.get("/users/me/", response_model=user_dm.User, tags=["users"])
def get_current_logged_in_user(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ):
    """
    Returns the information of current logged in user.
    """
    return current_user
