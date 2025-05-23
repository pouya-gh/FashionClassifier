from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session

from ..database.models import Task, User, APIKey
from ..database.db import get_db
from ..utils.auth import get_current_user
from ..data_models import task as task_dm

router = APIRouter()

@router.get("/my-tasks", response_model=List[task_dm.TaskInline])
async def get_user_tasks(
    api_key_id: Optional[int] = Query(None, description="Filter by API key ID"),
    state: Optional[Task.StateEnum] = Query(None, description="Filter by task state"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the list of tasks of the current user, optionally filtered by API key and state.

    - **api_key_id**: The unique identifier for the APIKey. This is not the same as API key itself.
    - **state**: State of the task. Is it processing or is it done?
    """
    # db_api_key = None
    # if api_key:
    #     db_api_key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.owner_id == current_user.id).first()
    #     if not db_api_key:
    #         raise HTTPException(
    #             status_code=404,
    #             detail="Api key not found. It either does not exist or it is not yours."
    #         )

    tasks = db.query(Task).filter(Task.user_id==current_user.id)
    if api_key_id:
        tasks = tasks.filter(Task.api_key_id == api_key_id)
    
    if state:
        tasks = tasks.filter(Task.state == state)

    return tasks.all()

@router.get("/my-tasks/{task_id}", response_model=task_dm.Task)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):
    """
    Retrieve a task by its ID.

    - **task_id**: The unique identifier for the task.
    """
    task = db.query(Task).filter(Task.user_id == current_user.id, Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    return task
