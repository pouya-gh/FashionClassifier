from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

APP_PATH = Path(__file__).resolve().parent

PYTORCH_MODEL_PATH = APP_PATH / "utils" / "data" / "mobilenet.pth"

TEMP_FILES_DIR = APP_PATH.parent / "temp_files"

API_KEY_NAME = "X-API-Key"
ALGORITHM = os.getenv("AUTH_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 600
SECRET_KEY = os.getenv("SECRET_KEY")

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
SQLALCHEMY_TEST_DATABASE_URL = os.getenv("SQLALCHEMY_TEST_DATABASE_URL")

CLASSIFY_RATE_LIMIT = 1 # Max 1 request
CLASSIFY_RATE_TIME_WINDOW = 10  # Per 10 seconds

SUPER_USER_USERNAME = os.getenv("SUPER_USER_USERNAME")
SUPER_USER_PASSWORD = os.getenv("SUPER_USER_PASSWORD")
SUPER_USER_EMAIL = os.getenv("SUPER_USER_EMAIL")

CELERY_BROKER=os.getenv("CELERY_BROKER")
CELERY_BACKEND=os.getenv("CELERY_BACKEND")

REDIS_HOST=os.getenv("REDIS_HOST")
REDIS_PORT=int(os.getenv("REDIS_PORT"))
REDIS_DB=int(os.getenv("REDIS_DB"))