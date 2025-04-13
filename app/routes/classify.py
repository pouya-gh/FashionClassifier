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

from ..utils.classifier import classify_image


router = APIRouter()

# Replace this with your actual API key
VALID_API_KEY = "your_secret_api_key"

def start_task(file_name: str, task_id: int):
    print(f"Processing file in the background: {file_name}")
    result = classify_image(file_name)
    print(f"Classification arg: {result}")

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
    
    task_instance = Task(api_key_id=api_key.id, filename=file_name)
    # Save the file or process it as needed
    file_name = file.filename
    db.add(task_instance)
    db.commit()
    db.refresh(task_instance)
    background_tasks.add_task(start_task, file_name, api_key.key)
    return {"message": "Background task started"}