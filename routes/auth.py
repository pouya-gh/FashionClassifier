from fastapi import APIRouter

from utils.auth import get_api_key, get_current_user

import secrets

router = APIRouter()

@router.get("/request")
async def status():
    return {"message": "Auth router is working!"}