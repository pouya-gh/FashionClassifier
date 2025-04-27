from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

PYTORCH_MODEL_PATH = Path(__file__).resolve().parent / "utils" / "data" / "mobilenet.pth"

API_KEY_NAME = "X-API-Key"
ALGORITHM = os.getenv("AUTH_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 600
SECRET_KEY = os.getenv("SECRET_KEY")

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
SQLALCHEMY_TEST_DATABASE_URL = os.getenv("SQLALCHEMY_TEST_DATABASE_URL")

CLASSIFY_RATE_LIMIT = 1 # Max 1 request
CLASSIFY_RATE_TIME_WINDOW = 10  # Per 10 seconds