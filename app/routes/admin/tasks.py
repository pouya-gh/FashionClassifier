from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.models import Task, User
from app.data_models import task as task_dm
from app.utils.auth import get_current_admin_user
from app.database.db import get_db

from typing import List
from datetime import datetime
from fastapi import Query

router = APIRouter(prefix="/admin", tags=["admin", "tasks"])


@router.get("/tasks", response_model=List[task_dm.TaskInlineAdmin])
async def get_tasks(
    user_id: int = None,
    # start_date: datetime = Query(None),
    # end_date: datetime = Query(None),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(Task)
    
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    
    # if start_date is not None:
    #     query = query.filter(Task.created_at >= start_date)
    
    # if end_date is not None:
    #     query = query.filter(Task.created_at <= end_date)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.get("/tasks/{task_id}", response_model=task_dm.TaskAdmin)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, f"Task with id {task_id} not found")
    
    return task

@router.patch("/tasks/{task_id}")
async def update_task(task_id: int, task: task_dm.TaskUpdate,
                      current_admin: User = Depends(get_current_admin_user),
                      db: Session = Depends(get_db)):
    update_data = task.model_dump(exclude_none=True)
    result = db.query(Task).filter(Task.id == task_id).update(update_data)
    db.commit()
    if result > 0:
        return {"message": "Task updated"}
    else:
        raise HTTPException(404, f"Task with id {task_id} not found")
    
@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int,
                      current_admin: User = Depends(get_current_admin_user),
                      db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, f"Task with id {task_id} not found")
    
    db.delete(task)
    db.commit()
    return {"message": f"Task {task_id} deleted."}
    