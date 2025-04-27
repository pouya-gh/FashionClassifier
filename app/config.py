from pathlib import Path


PYTORCH_MODEL_PATH = Path(__file__).resolve().parent / "utils" / "data" / "mobilenet.pth"

API_KEY_NAME = "X-API-Key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600
SECRET_KEY = "TST"

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./sql_test.db"

CLASSIFY_RATE_LIMIT = 1 # Max 1 request
CLASSIFY_RATE_TIME_WINDOW = 10  # Per 10 seconds