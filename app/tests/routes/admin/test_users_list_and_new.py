from fastapi.testclient import TestClient
from app.routes.admin.users import router
from app.database.models import User
from fastapi import FastAPI

from app.utils.auth import hash_password, authenticate_user, create_access_token
from app.utils.testing.testcase import MyTestCase
from app.database.db import get_db
from app.data_models import user as user_dm

from datetime import datetime, timedelta



app = FastAPI()
app.include_router(router)


client = TestClient(app)


class UsersAdminTests(MyTestCase):
    @classmethod
    def setTestData(cls):
        db = next(get_db())
    
        user = User(username="user1",
                email="mail@mail.com",
                hashed_password=hash_password("user1"),
                role=User.RoleEnum.admin)
        
        user2 = User(username="user2",
                email="mail2@mail.com",
                hashed_password=hash_password("user2"))
        
        in_active_user = User(username="user3",
                email="mail3@mail.com",
                hashed_password=hash_password("user3"),
                is_active=False)
        
        db.add_all([user, user2, in_active_user])
        db.commit()
        db.refresh(user)
        db.refresh(user2)

        cls.app = app

    def login_user(self, username, password):
        user = authenticate_user(self.db, username, password)
        if user:
            scopes = ["admin"] if user.role == User.RoleEnum.admin else []
            return create_access_token(
                data={"sub": username, "scopes": scopes},
                expires_delta=timedelta(minutes=30)
                )
        
        return ""

    def test_users_list_route_works(self):
        token = self.login_user(username="user1", password="user1")
        response = client.get("/admin/users",
                    headers={"Authorization": f"Bearer {token}"})
        
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(len(response.json()), 3)

    def test_users_list_route_works_with_admin_users(self):
        token = self.login_user(username="user2", password="user2")
        response = client.get("/admin/users",
                    headers={"Authorization": f"Bearer {token}"})
        
        self.assertEqual(response.status_code, 401, response.json())

    def test_users_list_route_filters_work(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/admin/users",
                    params={"role": "admin"},
                    headers=headers)
        
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(len(response.json()), 1)

        response = client.get("/admin/users",
                    params={"is_active": False},
                    headers=headers)
        
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(len(response.json()), 1)


    def test_users_list_route_pagination_works(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/admin/users",
                    params={"skip": "1"},
                    headers=headers)
        
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(len(response.json()), 2)

        response = client.get("/admin/users",
                    params={"limit": "1"},
                    headers=headers)
        
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(len(response.json()), 1)


        response = client.get("/admin/users",
                    params={"skip": "5"},
                    headers=headers)
        
        self.assertEqual(response.status_code, 404, response.json())

    def test_admin_add_new_user_route_works(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post("/admin/users/new",
                                json={
                                    "username": "user4",
                                    "email": "mail4@mail.com",
                                    "password": "user4"
                                },
                                headers=headers)
        
        self.assertEqual(response.status_code, 200, response.json())
        users_count = self.db.query(User).count()
        self.assertEqual(users_count, 4)

    def test_admin_add_new_user_route_works_when_admin_loggedin(self):
        token = self.login_user(username="user2", password="user2")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post("/admin/users/new",
                                json={
                                    "username": "user4",
                                    "email": "mail4@mail.com",
                                    "password": "user4"
                                },
                                headers=headers)
        
        self.assertEqual(response.status_code, 401, response.json())
        users_count = self.db.query(User).count()
        self.assertEqual(users_count, 3)

    def test_admin_add_new_user_route_fails_if_not_loggedin(self):
        response = client.post("/admin/users/new",
                                json={
                                    "username": "user4",
                                    "email": "mail4@mail.com",
                                    "password": "user4"
                                })
        
        self.assertEqual(response.status_code, 401, response.json())
        users_count = self.db.query(User).count()
        self.assertEqual(users_count, 3)