from fastapi import APIRouter, HTTPException, Depends

from app.database.models import User
from app.database.db import get_db
from app.data_models import user as user_dm
from app.utils.auth import get_current_admin_user

router = APIRouter(prefix="/admin",
                   tags=["admin", "users"],
                   dependencies=[Depends(get_current_admin_user)])

@router.get("/users", response_model=list[user_dm.User])
async def get_users(
    skip: int = 0, 
    limit: int = 10, 
    role: User.RoleEnum = None, 
    is_active: bool = None,
    db=Depends(get_db)
):
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if is_active is not None: # it is important this condition be written like this. because False means "only active users" but None means "dont filter by account state."
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users

@router.get("/users/{user_id}", response_model=user_dm.User)
async def get_user(
    user_id: int, 
    db=Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: user_dm.UserUpdate,
    db=Depends(get_db)
):
    update_data = user_update.model_dump(exclude_none=True)
    result = db.query(User).filter(User.id == user_id).update(update_data)
    db.commit()
    if result > 0:
        return {"message": "User info updated"}
    else:
        raise HTTPException(404, f"User with id {user_id} not found")

@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db=Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted."}