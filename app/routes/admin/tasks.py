from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.models import Task, User
from app.data_models import task as task_dm
from app.utils.auth import get_current_admin_user
from app.database.db import get_db

from typing import List
from datetime import datetime
from fastapi import Query

router = APIRouter(prefix="/admin")


@router.get("/tasks", response_model=List[task_dm.TaskInlineAdmin], tags=["admin", "tasks"])
async def get_tasks(
    user_id: int = None,
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(Task)
    
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    
    if start_date is not None:
        query = query.filter(Task.created_at >= start_date)
    
    if end_date is not None:
        query = query.filter(Task.created_at <= end_date)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks