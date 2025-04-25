from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from ..utils.auth import (get_current_user,
                          generate_api_key)
from ..database.db import get_db
from ..database.models import User, APIKey

from ..data_models import apikey as apikey_dm

from typing import Annotated, List
from datetime import timedelta, datetime

router = APIRouter()

@router.post("/api-keys/new", response_model=apikey_dm.APIKey)
def get_new_api_key(current_user: Annotated[User, Depends(get_current_user)],
                    db: Annotated[Session, Depends(get_db)]):
    #TODO: also check for api keys' expiry.  
    user_keys_count = db.query(APIKey).filter(APIKey.owner_id == current_user.id).count()
    if user_keys_count >= 5:
        raise HTTPException(
            status_code=400,
            detail="You have reached the maximum number of active api keys",
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

@router.delete("/my-api-keys/{key_id}", response_model=apikey_dm.APIKey)
def delete_api_key(key_id: int,
                   current_user: Annotated[User, Depends(get_current_user)],
                   db: Annotated[Session, Depends(get_db)]):
    api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.owner_id == current_user.id).first()
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or does not belong to the current user",
        )
    
    db.delete(api_key)
    db.commit()
    return api_key
