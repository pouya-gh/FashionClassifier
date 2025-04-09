from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db import Base
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
    is_active = Column(Integer, default=1)
    role = Column(Enum(RoleEnum), default=RoleEnum.normal, nullable=False)

    api_secrets = relationship("APISecret", backref="owner", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Integer, default=1)
    expiration_date = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="api_secrets")
    tasks = relationship("Task", backref="api_key", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    class StateEnum(enum.Enum):
        processing = "processing"
        done = "done"
        failed = "failed"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    api_key = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    state = Column(Enum(StateEnum), default=StateEnum.processing, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)