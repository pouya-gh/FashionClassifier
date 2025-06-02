from app.database.db import get_db
from app.database.models import Task
from celery import Celery
import redis
import json

from app.config import (REDIS_DB,
                        REDIS_HOST,
                        REDIS_PORT)

from app.utils.classifier import classify_image, FAHION_MNIST_CLASS_NAMES

from app.config import CELERY_BACKEND, CELERY_BROKER

import os

app = Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)

redis_connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

@app.task
def classify_task(task_id: int):
    """
    starts the background task of classifying images.

    - **task**: The Task instance creating when the request was received.
    - **db**: A database session for updating the instance.
    """
    db = next(get_db())
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
    redis_connection.publish(message_queue, json.dumps(message))

    print(f"Classification arg: {result}, ({FAHION_MNIST_CLASS_NAMES[result]})")
    os.remove(task.filename)