from fastapi.testclient import TestClient
from app.routes.tasks import router
from app.database.models import Task, APIKey, User
from sqlalchemy.orm import Session
from fastapi import FastAPI, Response

from app.utils.auth import API_KEY_NAME, hash_password, authenticate_user, create_access_token
from app.utils.testing.testcase import MyTestCase
from app.database.db import get_db

from datetime import datetime, timedelta



app = FastAPI()
app.include_router(router)


client = TestClient(app)

class ClassifierTests(MyTestCase):
    @classmethod
    def setTestData(cls):
        db = next(get_db())
    
        user = User(username="user1",
                email="mail@mail.com",
                hashed_password=hash_password("user1"))
        
        user2 = User(username="user2",
                email="mail2@mail.com",
                hashed_password=hash_password("user2"))
        db.add_all([user, user2])
        db.commit()
        db.refresh(user)
        db.refresh(user2)

        expiration_date = datetime.now() + timedelta(days=5)
        test_api_key = APIKey(key="test_key", expiration_date=expiration_date, owner_id=user.id)
        test_api_key_2 = APIKey(key="test_key_2", expiration_date=expiration_date, owner_id=user.id)
        test_api_key_3 = APIKey(key="test_key_3", expiration_date=expiration_date, owner_id=user2.id)

        db.add_all([test_api_key, test_api_key_2, test_api_key_3])
        db.commit()
        db.refresh(test_api_key)
        db.refresh(test_api_key_2)
        db.refresh(test_api_key_3)

        task1 = Task(api_key_id=test_api_key.id, filename="none", user_id=user.id)
        task2 = Task(api_key_id=test_api_key_2.id, filename="none", user_id=user.id)
        task3 = Task(api_key_id=test_api_key_3.id, filename="none", user_id=user2.id)

        db.add_all([task1, task2, task3])
        db.commit()
        cls.app = app

    def login_user(self, username, password):
        if authenticate_user(self.db, username, password):
            return create_access_token(
                data={"sub": username, "scopes": []},
                expires_delta=timedelta(minutes=30)
                )
        
        return ""

    def test_tasks_list_works(self):
        token = self.login_user(username="user1", password="user1")
        response = client.get("/tasks",
                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)

    def test_tasks_list_doesnt_work_if_not_loggedin(self):
        response = client.get("/tasks")

        self.assertEqual(response.status_code, 401)

    def test_tasks_list_only_loads_current_users_tasks(self):
        token = self.login_user(username="user1", password="user1")
        response = client.get("/tasks",
                    headers={"Authorization": f"Bearer {token}"})
        
        self.assertEqual(len(response.json()), 2)

    def test_tasks_list_filters_work(self):
        token = self.login_user(username="user1", password="user1")
        response = client.get("/tasks",
                              params={"api_key_id": 1},
                              headers={"Authorization": f"Bearer {token}"})
        
        self.assertEqual(len(response.json()), 1)

        response = client.get("/tasks",
                              params={"state": "done"},
                              headers={"Authorization": f"Bearer {token}"})
        
        self.assertEqual(len(response.json()), 0)


    def test_task_details_list_route_work(self):
        token = self.login_user(username="user1", password="user1")
        response = client.get("/tasks/1",
                              headers={"Authorization": f"Bearer {token}"})
        
        self.assertEqual(response.status_code, 200)

    def test_task_details_list_route_only_loads_current_users_tasks(self):
        token = self.login_user(username="user1", password="user1")
        response = client.get("/tasks/3",
                              headers={"Authorization": f"Bearer {token}"})
        
        self.assertEqual(response.status_code, 404)

    def test_task_details_list_route_works_only_loggedin(self):
        response = client.get("/tasks/1")
        
        self.assertEqual(response.status_code, 401)
