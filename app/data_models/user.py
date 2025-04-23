from pydantic import BaseModel, ConfigDict
from ..database.models import User as UserModel


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str | None = None
    is_active: bool
    role: UserModel.RoleEnum

class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    role: UserModel.RoleEnum | None = None