from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session


from ..utils.auth import (get_api_key,
                          get_current_user,
                          authenticate_user,
                          create_access_token,
                          get_current_active_user,
                          ACCESS_TOKEN_EXPIRE_MINUTES)
from ..database.db import get_db
from ..database.models import User

from typing import Annotated
from datetime import timedelta

router = APIRouter()

@router.get("/request")
async def status():
    return {"message": "Auth router is working!"}

@router.post("/token", tags=["authorization"])
def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[Session, Depends(get_db)]
    ):

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={'WWW-Authenticate': "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    scopes = []
    if user.is_superuser:
        scopes = ["super"]
    access_token = create_access_token(
        data={"sub": user.username, "scopes": scopes},
        expires_delta=access_token_expires
        )
    return {"access_token": access_token, "token_type":"bearer"}

@router.get("/users/me/", response_model=User, tags=["users"])
def get_current_logged_in_user(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ):

    return current_user
