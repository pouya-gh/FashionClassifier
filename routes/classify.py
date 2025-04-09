from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, status

router = APIRouter()

# Replace this with your actual API key
VALID_API_KEY = "your_secret_api_key"

def background_task(file_name: str):
    # Perform some background operation
    print(f"Processing file in the background: {file_name}")

@router.post("/classify")
async def classify(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_api_key: str = None
):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    if file.size > 512 * 1024:  # 512 KB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 512 KB limit"
        )
    
    # Save the file or process it as needed
    file_name = file.filename
    background_tasks.add_task(background_task, file_name)
    return {"message": "Background task started"}