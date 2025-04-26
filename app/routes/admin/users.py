from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.models import User
from app.database.db import get_db
from app.data_models import user as user_dm
from app.utils.auth import get_current_admin_user, hash_password

router = APIRouter(prefix="/admin",
                   tags=["admin", "users"],
                   dependencies=[Depends(get_current_admin_user)])

@router.get("/users", response_model=list[user_dm.User])
async def get_users(
    skip: int = 0, 
    limit: int = 10, 
    role: User.RoleEnum = None, 
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """
    Gets the list of users. The result can be filtered with user role and account activeness and also supports pagination.

    - **skip**: Skips the list of users by this amount. Used for pagination.
    - **limit**: Limits the number of results by this amount.
    - **role**: If set to a value, only returns the users of this role.
    - **is_active**: If set to a boolean value, filters the result by user activeness.
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if is_active is not None: # it is important this condition be written like this. because False means "only active users" but None means "dont filter by account state."
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users

@router.post("/users/new", response_model=user_dm.User)
async def create_user(user_data: user_dm.UserCreateAdmin,
                      db: Session = Depends(get_db)):
    """
    Creates a new user.

    - **user_data**: User data.
    """
    user_data_dict = user_data.model_dump(exclude_none=True)
    user_data_dict["hashed_password"] = hash_password(user_data_dict["password"])
    del user_data_dict["password"]

    user_instance = User(**user_data_dict)
    db.add(user_instance)
    db.commit()
    db.refresh(user_instance)

    return user_instance

@router.get("/users/{user_id}", response_model=user_dm.User)
async def get_user(
    user_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get a user's information.

    - **user_id**: User's unique identifier.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: user_dm.UserUpdateAdmin,
    db: Session = Depends(get_db)
):
    """
    Updates a user informations.

    - **user_id**: User's unique identifier.
    - **user_data**: User data.
    """
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
    db: Session = Depends(get_db)
):
    """
    Deletes a user. This **does not** ask for confirmation. Use with caution.

    - **user_id**: User's unique identifier.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted."}