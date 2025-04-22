from pydantic import BaseModel, ConfigDict
from ..database import models

from datetime import datetime

class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state: models.Task.StateEnum
    result: int
    created_at: datetime
    updated_at: datetime

class TaskAdmin(Task):
    model_config = ConfigDict(from_attributes=True)

    user_id: int

class TaskInline(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state: models.Task.StateEnum
    result: int

class TaskInlineAdmin(TaskInline):
    model_config = ConfigDict(from_attributes=True)

    user_id: int

class TaskUpdate(BaseModel):
    state: models.Task.StateEnum | None = None
    result: int | None = None