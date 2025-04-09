from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from ..database.db import get_db
from ..database.models import APIKey



API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header), db: Session = Depends(get_db)):
    if api_key_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header is missing"
        )
    api_key = db.query(APIKey).filter(APIKey.key == api_key_header).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key_header

async def get_current_user(api_key: str = Security(get_api_key), db: Session = Depends(get_db)):
    # Fetch user data based on the API key from the database
    api_key_entry = db.query(APIKey).filter(APIKey.key == api_key).first()
    if api_key_entry and api_key_entry.user:
        return api_key_entry.user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

# Add this dependency to any route that needs API Key protection
# Example: @app.get("/protected", dependencies=[Depends(get_api_key)])