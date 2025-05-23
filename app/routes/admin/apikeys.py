from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.models import APIKey
from app.database.db import get_db
from app.data_models import apikey as apikey_dm
from app.utils.auth import get_current_admin_user, generate_api_key

router = APIRouter(prefix="/admin",
                   tags=["admin", "apikeys"],
                   dependencies=[Depends(get_current_admin_user)])

@router.get("/apikeys", response_model=list[apikey_dm.APIKeyAdmin])
async def get_apikeys(
    skip: int = 0, 
    limit: int = 10, 
    is_active: bool = None,
    owner_id: int = None,
    db=Depends(get_db)
):
    """
    Gets the list of API keys. The result can be filtered with user ID and activeness and also supports pagination.

    - **skip**: Skips the list of API keys by this amount. Used for pagination.
    - **limit**: Limits the number of results by this amount.
    - **owner_id**: If set to a value, only returns the API keys of the specified user.
    - **is_active**: If set to a boolean value, the results will be filtered by key's activeness.
    """
    query = db.query(APIKey)
    
    if is_active is not None:
        query = query.filter(APIKey.is_active == is_active)
    
    if owner_id is not None:
        query = query.filter(APIKey.owner_id == owner_id)
    
    apikeys = query.offset(skip).limit(limit).all()
    if not apikeys:
        raise HTTPException(status_code=404, detail="No API keys found")
    return apikeys

@router.post("/apikeys/new", response_model=apikey_dm.APIKeyAdmin)
async def create_apikey(
    apikey_data: apikey_dm.APIKeyCreate,
    db: Session = Depends(get_db)
):
    """
    Creates a new API key.

    - **apikey_data**: Key data.
    """
    apikey_data_dict = apikey_data.model_dump(exclude_none=True)
    apikey_data_dict["key"] = generate_api_key()

    apikey_instance = APIKey(**apikey_data_dict)
    db.add(apikey_instance)
    db.commit()
    db.refresh(apikey_instance)

    return apikey_instance

@router.get("/apikeys/{apikey_id}", response_model=apikey_dm.APIKeyAdmin)
async def get_apikey(
    apikey_id: int, 
    db=Depends(get_db)
):
    """
    Get an API key's information.

    - **apikey_id**: API keys's unique identifier.
    """
    apikey = db.query(APIKey).filter(APIKey.id == apikey_id).first()
    if not apikey:
        raise HTTPException(status_code=404, detail="API key not found")
    return apikey

@router.patch("/apikeys/{apikey_id}")
async def update_apikey(
    apikey_id: int,
    apikey_update: apikey_dm.APIKeyUpdate,
    db=Depends(get_db)
):
    """
    Updates a API key's informations.

    - **apikey_id**: API key's unique identifier.
    - **apikey_update**: API key data.
    """
    update_data = apikey_update.model_dump(exclude_none=True)
    result = db.query(APIKey).filter(APIKey.id == apikey_id).update(update_data)
    db.commit()
    if result > 0:
        return {"message": "API key info updated"}
    else:
        raise HTTPException(404, f"API key with id {apikey_id} not found")

@router.delete("/apikeys/{apikey_id}", status_code=204)
async def delete_apikey(
    apikey_id: int,
    db=Depends(get_db)
):
    """
    Deletes an API key. This **does not** ask for confirmation. Use with caution.

    - **apikey_id**: API key's unique identifier.
    """
    apikey = db.query(APIKey).filter(APIKey.id == apikey_id).first()
    if not apikey:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(apikey)
    db.commit()
    return {"message": f"API key {apikey_id} deleted."}
