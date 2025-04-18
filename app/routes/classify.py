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


router = APIRouter()

# Replace this with your actual API key
VALID_API_KEY = "your_secret_api_key"

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
    
    # file_path = Path("temp_file") / api_key.owner.username
    # file_path /= file.filename
    file_path = file.filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    task_instance = Task(api_key_id=api_key.id, filename=file_path)
    db.add(task_instance)
    db.commit()
    db.refresh(task_instance)
    background_tasks.add_task(start_task, task_instance, db)
    return {"message": "Background task started"}