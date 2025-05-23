from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base
import enum


class User(Base):
    __tablename__ = 'users'

    class RoleEnum(enum.Enum):
        normal = "normal"
        verified = "verified"
        admin = "admin"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.normal, nullable=False)

    api_keys = relationship("APIKey", backref="owner", cascade="all, delete-orphan")
    tasks = relationship("Task", backref="user", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True, index=True) # this is not redundant. this is used for admin api requests. 
                                                       # otherwise, clients would need to send the whole key as a get
                                                       # argument in every request which would not the most secure design choice.
    key = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    expiration_date = Column(DateTime, nullable=True)

    tasks = relationship("Task", backref="api_key", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    class StateEnum(enum.Enum):
        processing = "processing"
        done = "done"
        failed = "failed"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    state = Column(Enum(StateEnum), default=StateEnum.processing, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)
    result = Column(Integer, default=-1)