from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import SQLALCHEMY_TEST_DATABASE_URL

# import os

# if os.getenv("ENVIRONMENT", default="dev") == "test":
#     SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_test.db"
# else:
#     SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# # Database configuration
# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()