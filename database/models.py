from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from db import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Integer, default=1)

    api_secrets = relationship("APISecret", backref="owner", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = 'api_key'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Integer, default=1)
    expiration_date = Column(String, nullable=True)