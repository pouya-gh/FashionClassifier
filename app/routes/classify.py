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

from app.config import (CLASSIFY_RATE_LIMIT,
                        CLASSIFY_RATE_TIME_WINDOW,
                        TEMP_FILES_DIR,
                        REDIS_DB,
                        REDIS_HOST,
                        REDIS_PORT)

from app.tasks import classify_task

import os
import uuid
from time import time

import redis

redis_connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
# request_counts_by_ip = {}
# request_counts_by_api_key = {}
# RATE_LIMIT = 1 # Max 1 request
# TIME_WINDOW = 10  # Per 10 seconds


async def ip_rate_limiter(request: Request):
    """
    A simple memory based rate limiter which limits the requests per minute per IP address.
    This is meant to be used as dependency not as a middleware since not all path operations 
    need to be rate limited.
    """
    
    redis_key = "iplimiter:" + request.client.host
    current_time = time()

    if bool(redis_connection.exists(redis_key)):
        prev_req_times = redis_connection.lrange(redis_key, 0, -1)
       
        sorted_reqs = [
            timestamp for timestamp in prev_req_times if current_time - float(timestamp) < CLASSIFY_RATE_TIME_WINDOW
        ]

        if len(sorted_reqs) >= CLASSIFY_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests from your ip")
        
        # remove older request time stamps
        for _ in range(len(prev_req_times) - len(sorted_reqs)):
            redis_connection.rpop(redis_key)

    # Add current request timestamp
    redis_connection.lpush(redis_key, current_time)

async def api_key_rate_limiter(api_key: APIKey = Security(get_api_key)):
    """
    A simple memory based rate limiter which limits the requests per minute per api key.
    This is meant to be used as dependency not as a middleware since not all path operations 
    need to be rate limited.
    """

    redis_key = "apikeylimiter:" + str(api_key.id)
    current_time = time()

    if bool(redis_connection.exists(redis_key)):
        prev_req_times = redis_connection.lrange(redis_key, 0, -1)
       
        sorted_reqs = [
            timestamp for timestamp in prev_req_times if current_time - float(timestamp) < CLASSIFY_RATE_TIME_WINDOW
        ]

        if len(sorted_reqs) >= CLASSIFY_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests from your ip")
        
        # remove older request time stamps
        for _ in range(len(prev_req_times) - len(sorted_reqs)):
            redis_connection.rpop(redis_key)

    # Add current request timestamp
    redis_connection.lpush(redis_key, current_time)


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
    # background_tasks.add_task(start_task, task_instance, db)
    classify_task.delay(task_instance.id)
    return {"message": f"Request queued with id {task_instance.id}! Check your tasks for the result."}