from pydantic import BaseModel, ConfigDict
from ..database.models import User


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    fullname: str | None = None
    is_active: bool
    role: User.RoleEnum