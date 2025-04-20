from pydantic import BaseModel, ConfigDict
from ..database.models import Task

from datetime import datetime

class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state: str
    result: int
    created_at: datetime
    updated_at: datetime

class TaskInline(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state: str
    result: int