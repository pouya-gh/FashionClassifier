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
from app.config import (API_KEY_NAME,
                        ALGORITHM,
                        SECRET_KEY)

class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='token',
    scopes={"admin": "permission to perform administrator action"},)

async def get_api_key(api_key_header: str = Depends(api_key_header),
                      db: Session = Depends(get_db)) -> APIKey:
    """
    This dependency is used to get api key from a header provided by user.
    If the key has expired, Raises an HTTP exception.


    Returns:
    APIKey: An object which is an instance of APIKey model.
    """
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

async def get_current_user_by_api_key(api_key: APIKey = Security(get_api_key)) -> User:
    # Fetch user data based on the API key from the database
    """
    This dependency fetchs user data based on the API key from the database.
    If the key has expired, Raises an HTTP exception.

    Returns:
    User: An object which is an instance of User model.
    """
    if api_key.user:
        return api_key.user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


def hash_password(password) -> bytes:
    """
    Hashes a password for storing in database.

    - **password**: The password as string in utf-8 encoding.

    Returns:
    bytes: hashed password.
    """
    password_as_bytes = bytes(password, "utf-8")
    return bcrypt.hashpw(password_as_bytes, bcrypt.gensalt()).decode("utf-8")

def check_password(password, hashed_password) -> bool:
    """
    Checks a password againts a hash to see if they match.

    - **password**: The password as string in utf-8 encoding.
    - **hashed_password**: The hashed password as string in utf-8 encoding.
    """
    password_as_bytes = bytes(password, 'utf-8')
    hashed_password_as_bytes = bytes(hashed_password, 'utf-8')
    return bcrypt.checkpw(password_as_bytes, 
                          hashed_password_as_bytes)

def authenticate_user(db: Session, username: str, password: str) -> User | bool:
    """
    Authenticates a user with username and password. If successfull returns an instance
    of User model otherwise, it returns false.

    - **db**: A database session.
    - **username**: Username.
    - **password**: The password as string in utf-8 encoding.

    Returns:
    User | False: If successful, An object which is an instance of User model. Returns false otherwise.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not check_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict,
                        expires_delta: timedelta | None = None) -> str:
    """
    Creates an access token from a dictionary of data and sets its expiry.

    - **data**: A dictionary containing the data.
    - **expires_delta**: An optional expiration time delta. If not provided, it is set to 15 minutes.

    Returns:
    str: Encoded data.
    """
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
        db: Annotated[Session, Depends(get_db)]) -> User:
    """
    A dependency for authenticating user using password scheme.

    Returns:
    User: Current user.
    """
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
                detail="You don't have the premission to use this feature.",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user

def get_current_admin_user(
        current_user: Annotated[User, Security(get_current_user, scopes=["admin"])]
        ) -> User:
    """
    A shorthand dependency for authenticating ""admin"" users using password scheme.

    Returns:
    User: Current user.
    """
    return current_user

def get_current_active_user(
        current_user: Annotated[User, Security(get_current_user)]
        ) -> User:
    """
    A shorthand dependency for authenticating ""active"" users using password scheme.

    Returns:
    User: Current user.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def generate_api_key() -> str:
    """
    Returns a newly generated token for api keys.

    Returns:
    str: generated api key.
    """
    return secrets.token_hex(32)