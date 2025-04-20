from pydantic import BaseModel, ConfigDict

from datetime import datetime

class APIKey(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    is_active: bool
    expiration_date: datetime