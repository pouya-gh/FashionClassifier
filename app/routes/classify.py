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
from app.routes.notifications import connected_clients_queues

from app.config import (CLASSIFY_RATE_LIMIT,
                        CLASSIFY_RATE_TIME_WINDOW,
                        TEMP_FILES_DIR)

import os
import uuid
from time import time


from app.utils.classifier import classify_image, FAHION_MNIST_CLASS_NAMES


ip_rate_limiter_dict = {}
key_rate_limiter_dict = {}

def classify_task(task_id: int, db: Session):
    """
    Classifies The image and informs the user about the result with notifications

    - **task**: The Task instance creating when the request was received.
    - **db**: A database session for updating the instance.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return
    
    message_queue = f"taskmessages:{task.user_id}"

    print(f"Processing file in the background: {task.filename}")
    result = classify_image(task.filename)
    task.result = result
    task.state = Task.StateEnum.done
    db.commit()
    message = {
        "event": "classification_completed",
        "retry": 3000,
        "data": f"Task {task.id} finished. Result: {FAHION_MNIST_CLASS_NAMES[result]}({result})",
    }
    # inform the notification service
    client_queue = connected_clients_queues.get(message_queue)
    if client_queue:
        client_queue.put_nowait(message)

    print(f"Classification arg: {result}, ({FAHION_MNIST_CLASS_NAMES[result]})")
    os.remove(task.filename)


async def ip_rate_limiter(request: Request):
    """
    A simple memory based rate limiter which limits the requests per minute per IP address.
    This is meant to be used as dependency not as a middleware since not all path operations 
    need to be rate limited.
    """
    
    ip = request.client.host
    current_time = time()

    if ip in ip_rate_limiter_dict:
        prev_req_times = ip_rate_limiter_dict[ip]

        sorted_reqs = [
            timestamp for timestamp in prev_req_times if current_time - float(timestamp) < CLASSIFY_RATE_TIME_WINDOW
        ]

        if len(sorted_reqs) >= CLASSIFY_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests from your ip")
        
        # remove older request time stamps
        for _ in range(len(prev_req_times) - len(sorted_reqs)):
            ip_rate_limiter_dict[ip].pop(0)
        
        ip_rate_limiter_dict[ip].append(current_time)
    else:
        ip_rate_limiter_dict[ip] = [current_time]


async def api_key_rate_limiter(api_key: APIKey = Security(get_api_key)):
    """
    A simple memory based rate limiter which limits the requests per minute per api key.
    This is meant to be used as dependency not as a middleware since not all path operations 
    need to be rate limited.
    """

    key_id = str(api_key.id)
    current_time = time()

    if key_id in key_rate_limiter_dict:
        prev_req_times = key_rate_limiter_dict[key_id]

        sorted_reqs = [
            timestamp for timestamp in prev_req_times if current_time - float(timestamp) < CLASSIFY_RATE_TIME_WINDOW
        ]

        if len(sorted_reqs) >= CLASSIFY_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests from your ip")
        
        # remove older request time stamps
        for _ in range(len(prev_req_times) - len(sorted_reqs)):
            key_rate_limiter_dict[key_id].pop(0)
        
        key_rate_limiter_dict[key_id].append(current_time)

    else:
        key_rate_limiter_dict[key_id] = [current_time]

router = APIRouter()



def _prepare_file(dir_path, file):
    os.makedirs(dir_path, exist_ok=True)
    
    file_path = dir_path / str(uuid.uuid1())
    with open(file_path, "wb") as f:
        f.write(file.read())

    return file_path

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
    
    dir_path = TEMP_FILES_DIR / api_key.owner.username

    file_path = _prepare_file(dir_path, file.file)

    task_instance = Task(user_id=api_key.owner.id, api_key_id=api_key.id, filename=str(file_path))
    db.add(task_instance)
    db.commit()
    db.refresh(task_instance)
    background_tasks.add_task(classify_task, task_instance.id, db)
    # classify_task.delay(task_instance.id)
    return {"message": f"Request queued with id {task_instance.id}! Check your tasks for the result."}