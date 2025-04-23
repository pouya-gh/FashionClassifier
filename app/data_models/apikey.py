from pydantic import BaseModel, ConfigDict

from datetime import datetime

class APIKey(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    is_active: bool
    expiration_date: datetime

class APIKeyAdmin(APIKey):
    owner_id: int

class APIKeyUpdate(BaseModel):
    key: str | None = None
    is_active: bool | None = None
    expiration_date: datetime | None = None

class APIKeyCreate(BaseModel):
    owner_id: int
    is_active: bool = True
    expiration_date: datetime