from fastapi.testclient import TestClient
from app.routes.classify import router
from app.database.models import Task, APIKey, User
from unittest.mock import patch
from fastapi import FastAPI, Response

from app.utils.auth import API_KEY_NAME, hash_password
from app.utils.testing.testcase import MyTestCase
from app.utils.testing.database import get_test_db

from datetime import datetime, timedelta

app = FastAPI()
app.include_router(router)


client = TestClient(app)

class ClassifierTests(MyTestCase):
    @classmethod
    def setTestData(cls):
        db = next(get_test_db())
    
        user = User(username="user1",
                email="mail@mail.com",
                hashed_password=hash_password("user1"))
        db.add(user)
        db.commit()
        db.refresh(user)

        test_api_key = APIKey(key="test_key", expiration_date=datetime.now() + timedelta(days=5), owner_id=user.id)
        db.add(test_api_key)
        db.commit()
        db.refresh(test_api_key)

        cls.app = app

    @patch('app.routes.classify._prepare_file')
    @patch('app.routes.classify.start_task') 
    def test_classify_works_with_valid_data(self, start_task, _prepare_file):
        with open("app/tst.png", "rb") as f:
            response: Response = client.post("/classify",
                            files={"file": ("test_image.png", f.read())},
                            headers={API_KEY_NAME: "test_key"})
    
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Request queued with id 1! Check your tasks for the result."})
        tasks_count = self.db.query(Task).count()
        self.assertEqual(tasks_count, 1)

    @patch('app.routes.classify._prepare_file')
    @patch('app.routes.classify.start_task') 
    def test_classify_fails_without_valid_api_key(self, start_task, _prepare_file):
        with open("app/tst.png", "rb") as f:
            response: Response = client.post("/classify",
                            files={"file": ("test_image.png", f.read())},
                            headers={API_KEY_NAME: "bad_api_key"})
    
        self.assertEqual(response.status_code, 403)
        tasks_count = self.db.query(Task).count()
        self.assertEqual(tasks_count, 0)

