from app.database.db import get_db
from app.database.models import Task
from celery import Celery

from app.utils.classifier import classify_image, FAHION_MNIST_CLASS_NAMES

from app.config import CELERY_BACKEND, CELERY_BROKER

import os

app = Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)


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
    print(f"Processing file in the background: {task.filename}")
    result = classify_image(task.filename)
    task.result = result
    task.state = Task.StateEnum.done
    db.commit()
    print(f"Classification arg: {result}, ({FAHION_MNIST_CLASS_NAMES[result]})")
    os.remove(task.filename)