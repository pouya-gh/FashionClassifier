from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session


from ..utils.auth import (get_api_key,
                          hash_password,
                          get_current_user,
                          authenticate_user,
                          create_access_token,
                          get_current_active_user,
                          ACCESS_TOKEN_EXPIRE_MINUTES,
                          generate_api_key)
from ..database.db import get_db
from ..database.models import User, APIKey

from ..data_models import user as user_dm
from ..data_models import apikey as apikey_dm

from typing import Annotated, List
from datetime import timedelta, datetime

router = APIRouter()

@router.get("/request")
async def status():
    return {"message": "Auth router is working!"}

@router.post("/users/new", response_model=user_dm.User)
async def user_signup(username: str, password: str, email: str, db: Annotated[Session, Depends(get_db)]):
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

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={'WWW-Authenticate': "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    scopes = []
    # if user.is_superuser:
    #     scopes = ["super"]
    access_token = create_access_token(
        data={"sub": user.username, "scopes": scopes},
        expires_delta=access_token_expires
        )
    return {"access_token": access_token, "token_type":"bearer"}

@router.get("/users/me/", response_model=user_dm.User, tags=["users"])
def get_current_logged_in_user(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ):

    return current_user

@router.post("/api-keys/new", response_model=apikey_dm.APIKey)
def get_new_api_key(current_user: Annotated[User, Depends(get_current_user)],
                    db: Annotated[Session, Depends(get_db)]):
    #TODO: also check for api keys' expiry.  
    user_keys_count = db.query(APIKey).filter(APIKey.owner_id == current_user.id).count()
    if user_keys_count >= 5:
        raise HTTPException(
            status_code=400,
            detail="You have reached the number of active api keys",
        )
    
    new_key = APIKey(key=generate_api_key(),
                     owner_id=current_user.id,
                     expiration_date=datetime.now() + timedelta(days=5))
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    return new_key

@router.get("/my-api-keys", response_model=List[apikey_dm.APIKey])
def get_current_user_api_keys(current_user: Annotated[User, Depends(get_current_user)],
                    db: Annotated[Session, Depends(get_db)],
                    active_only: bool = False):
    result = db.query(APIKey).filter(APIKey.owner_id == current_user.id)
    if active_only:
        result = result.filter(APIKey.is_active == True)

    return result.all()