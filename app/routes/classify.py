from fastapi import (APIRouter,
                     BackgroundTasks,
                     HTTPException,
                     UploadFile,
                     File,
                     status,
                     Security,
                     Depends)
from sqlalchemy.orm import Session

from ..database.models import APIKey, Task
from ..database.db import get_db
from ..utils.auth import get_api_key

from ..utils.classifier import classify_image, FAHION_MNIST_CLASS_NAMES

import os
from pathlib import Path
import uuid

router = APIRouter()

def start_task(task: Task, db: Session):
    print(f"Processing file in the background: {task.filename}")
    result = classify_image(task.filename)
    task_db = db.query(Task).filter(Task.id==task.id)
    task_db.update({"result": result, "state": Task.StateEnum.done})
    db.commit()
    print(f"Classification arg: {result}, ({FAHION_MNIST_CLASS_NAMES[result]})")
    os.remove(task.filename)

@router.post("/classify")
async def classify(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    api_key: APIKey = Security(get_api_key)
):
    
    if file.size > 512 * 1024:  # 512 KB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 512 KB limit"
        )
    
    file_path = Path("temp_files") / api_key.owner.username

    os.makedirs(file_path, exist_ok=True)
    
    file_path /= str(uuid.uuid1())
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    task_instance = Task(user_id=api_key.owner.id, api_key_id=api_key.id, filename=str(file_path))
    db.add(task_instance)
    db.commit()
    db.refresh(task_instance)
    background_tasks.add_task(start_task, task_instance, db)
    return {"message": "Background task started"}