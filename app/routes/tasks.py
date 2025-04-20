from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session

from ..database.models import Task, User, APIKey
from ..database.db import get_db
from ..utils.auth import get_current_user
from ..data_models import task as task_dm

router = APIRouter()

@router.get("/tasks", response_model=List[task_dm.TaskInline])
async def get_user_tasks(
    api_key: Optional[str] = Query(None, description="Filter by API key"),
    state: Optional[Task.StateEnum] = Query(None, description="Filter by task state"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the list of tasks for the current user, optionally filtered by API key and state.
    """
    db_api_key = None
    if api_key:
        db_api_key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.owner_id == current_user.id).first()
        if not db_api_key:
            raise HTTPException(
                status_code=404,
                detail="Api key not found. It either does not exist or it is not yours."
            )

    tasks = db.query(Task)
    if api_key:
        tasks = tasks.filter(Task.api_key_id == db_api_key.id)
    
    if state:
        tasks = tasks.filter(Task.state == state)

    return tasks.all()

@router.get("/tasks/{task_id}", response_model=task_dm.Task)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    task = db.query(Task).filter(Task.user_id == current_user.id, Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    return task
