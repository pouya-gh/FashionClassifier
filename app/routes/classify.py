from fastapi import (APIRouter,
                     BackgroundTasks,
                     HTTPException,
                     UploadFile,
                     File,
                     Security,
                     Depends,
                     Request)
from sqlalchemy.orm import Session

from ..database.models import APIKey, Task
from ..database.db import get_db
from ..utils.auth import get_api_key

from ..utils.classifier import classify_image, FAHION_MNIST_CLASS_NAMES
from app.config import CLASSIFY_RATE_LIMIT, CLASSIFY_RATE_TIME_WINDOW

import os
from pathlib import Path
import uuid
from time import time


request_counts_by_ip = {}
request_counts_by_api_key = {}
# RATE_LIMIT = 1 # Max 1 request
# TIME_WINDOW = 10  # Per 10 seconds


async def ip_rate_limiter(request: Request):
    # if os.getenv("ENVIRONMENT", default="dev") == "test":
    #     return

    client_ip = request.client.host
    current_time = time()

    if client_ip in request_counts_by_ip:
        request_times = request_counts_by_ip[client_ip]

        # Remove outdated requests outside the time window
        request_counts_by_ip[client_ip] = [
            timestamp for timestamp in request_times if current_time - timestamp < CLASSIFY_RATE_TIME_WINDOW
        ]

        if len(request_counts_by_ip[client_ip]) >= CLASSIFY_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests from your ip")

    # Add current request timestamp
    request_counts_by_ip.setdefault(client_ip, []).append(current_time)

async def api_key_rate_limiter(api_key: APIKey = Security(get_api_key)):
    # if os.getenv("ENVIRONMENT", default="dev") == "test":
    #     return
    
    client_api_key = api_key.key
    current_time = time()

    if client_api_key in request_counts_by_api_key:
        request_times = request_counts_by_api_key[client_api_key]

        # Remove outdated requests outside the time window
        request_counts_by_api_key[client_api_key] = [
            timestamp for timestamp in request_times if current_time - timestamp < CLASSIFY_RATE_TIME_WINDOW
        ]

        if len(request_counts_by_api_key[client_api_key]) >= CLASSIFY_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests by your api key")

    # Add current request timestamp
    request_counts_by_api_key.setdefault(client_api_key, []).append(current_time)


router = APIRouter()


def start_task(task: Task, db: Session):
    print(f"Processing file in the background: {task.filename}")
    result = classify_image(task.filename)
    task_db = db.query(Task).filter(Task.id==task.id)
    task_db.update({"result": result, "state": Task.StateEnum.done})
    db.commit()
    print(f"Classification arg: {result}, ({FAHION_MNIST_CLASS_NAMES[result]})")
    os.remove(task.filename)

@router.post("/classify", dependencies=[Depends(ip_rate_limiter), Depends(api_key_rate_limiter)])
async def classify(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    api_key: APIKey = Security(get_api_key)
):
    """
    Classify an image of clothing. The classes are limited to Fashion-MNIST classes.
    Works best when the image is not worn by a person and is on a contrasting background.
    For example, if the color of a shirt is black, the background must be a bright color, preferably white.

    - **file**: The image file. Images must be less than 512 KB in size.
    """
    if file.size > 512 * 1024:  # 512 KB
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 512 KB limit"
        )
    
    # for performance reasons only one running task is allowed.
    number_of_running_tasks = db.query(Task).filter(Task.state == Task.StateEnum.processing).count()
    if number_of_running_tasks > 0:
        raise HTTPException(503, "Task queue is full. Try another time.")
    
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
    return {"message": f"Request queued with id {task_instance.id}! Check your tasks for the result."}