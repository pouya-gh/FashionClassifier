from fastapi.testclient import TestClient
from app.routes.apikeys import router
from app.database.models import APIKey, User
from fastapi import FastAPI

from app.utils.auth import hash_password, authenticate_user, create_access_token
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

        test_api_key = APIKey(key="test_key", expiration_date=datetime.now() + timedelta(days=5), owner_id=user.id)
        db.add(test_api_key)
        db.commit()
        db.refresh(test_api_key)

        cls.app = app

    def login_user(self, username, password):
        if authenticate_user(self.db, username, password):
            return create_access_token(
                data={"sub": username, "scopes": []},
                expires_delta=timedelta(minutes=30)
                )
        
        return ""

    def test_my_api_keys_route_works(self):
        token = self.login_user(username="user1", password="user1")
        response = client.get("/my-api-keys",
                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_my_api_keys_route_works_only_loggedin(self):
        response = client.get("/my-api-keys")

        self.assertEqual(response.status_code, 401)

    def test_my_api_keys_only_loads_current_users_keys(self):
        token = self.login_user(username="user2", password="user2")
        response = client.get("/my-api-keys",
                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_new_api_key_route_works(self):
        token = self.login_user(username="user1", password="user1")
        response = client.post("/api-keys/new",
                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200, response.json())
        apikey_count = self.db.query(APIKey).filter(APIKey.owner_id == 1).count()
        self.assertEqual(apikey_count, 2)

    def test_new_api_key_route_works_only_loggedin(self):
        response = client.post("/api-keys/new")

        self.assertEqual(response.status_code, 401, response.json())

    def test_new_api_key_route_doesnt_create_more_than_5_each_user(self):
        token = self.login_user(username="user1", password="user1")
        user1_headers = {"Authorization": f"Bearer {token}"}
        token_user2 = self.login_user(username="user2", password="user2")
        client.post("/api-keys/new", headers=user1_headers)
        client.post("/api-keys/new", headers=user1_headers)
        client.post("/api-keys/new", headers=user1_headers)
        response_4 = client.post("/api-keys/new", headers=user1_headers)
        response_5 = client.post("/api-keys/new", headers=user1_headers)

        response_user2 = client.post("/api-keys/new",
                                     headers={"Authorization": f"Bearer {token_user2}"})

        self.assertEqual(response_4.status_code, 200, response_4.json())
        self.assertEqual(response_5.status_code, 400, response_4.json())
        self.assertEqual(response_user2.status_code, 200, response_4.json())

    def test_delete_api_key_route_works(self):
        token = self.login_user(username="user1", password="user1")
        response = client.delete("/my-api-keys/1",
                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        apikey_count = self.db.query(APIKey).filter(APIKey.owner_id == 1).count()
        self.assertEqual(apikey_count, 0)

    def test_delete_api_key_route_works_only_loggedin(self):
        response = client.delete("/my-api-keys/1")

        self.assertEqual(response.status_code, 401)