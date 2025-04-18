from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from sqlalchemy.orm import Session
from pydantic import ValidationError, BaseModel

from datetime import timedelta, datetime, timezone
import secrets
import jwt
import bcrypt
from typing import Annotated

from ..database.db import get_db
from ..database.models import APIKey, User


API_KEY_NAME = "X-API-Key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "TST"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str, db: Session = Depends(get_db)):
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
    
    if api_key.expiration_date and api_key.expiration_date < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key has expired!"
        )
    return api_key

async def get_current_user_by_api_key(api_key: APIKey = Security(get_api_key), db: Session = Depends(get_db)):
    # Fetch user data based on the API key from the database
    if api_key.user:
        return api_key.user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

# Add this dependency to any route that needs API Key protection
# Example: @app.get("/protected", dependencies=[Depends(get_api_key)])

class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='token',
    scopes={"super": "permission to perform administrator action"},)

def hash_password(password):
    password_as_bytes = bytes(password, "utf-8")
    return bcrypt.hashpw(password_as_bytes, bcrypt.gensalt()).decode("utf-8")

def check_password(password, hashed_password):
    password_as_bytes = bytes(password, 'utf-8')
    hashed_password_as_bytes = bytes(hashed_password, 'utf-8')
    return bcrypt.checkpw(password_as_bytes, 
                          hashed_password_as_bytes)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not check_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
        security_scopes: SecurityScopes,
        token: Annotated[str, Depends(oauth2_scheme)], 
        db: Annotated[Session, Depends(get_db)]):
    
    if security_scopes.scopes:
        authenticate_value = f"Bearer scopes=\"{security_scopes.scope_str}\""
    else:
        authenticate_value = "Bearer"
    credintials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credintials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except (jwt.exceptions.InvalidTokenError, ValidationError):
        raise credintials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credintials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
                        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user

def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
        ):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def generate_api_key():
    """
    Returns a newly generated token for api keys.
    """
    return secrets.token_hex(32)