from fastapi.testclient import TestClient
from app.routes.admin.users import router
from app.database.models import User
from fastapi import FastAPI

from app.utils.auth import hash_password, authenticate_user, create_access_token
from app.utils.testing.testcase import MyTestCase
from app.utils.testing.database import get_test_db

from datetime import timedelta



app = FastAPI()
app.include_router(router)


client = TestClient(app)


class UsersAdminDetailsUpdateDeleteTests(MyTestCase):
    @classmethod
    def setTestData(cls):
        db = next(get_test_db())
    
        user = User(username="user1",
                email="mail@mail.com",
                hashed_password=hash_password("user1"),
                role=User.RoleEnum.admin)
        
        user2 = User(username="user2",
                email="mail2@mail.com",
                hashed_password=hash_password("user2"))
        
        inactive_user = User(username="user3",
                email="mail3@mail.com",
                hashed_password=hash_password("user3"),
                is_active=False)
        
        db.add_all([user, user2, inactive_user])
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

    def test_admin_get_user_details_route_works(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/admin/users/1",
                                headers=headers)
        
        self.assertEqual(response.status_code, 200, response.json())

        response = client.get("/admin/users/1")
        
        self.assertEqual(response.status_code, 401, "This shouldn't work it not logged in.")

    def test_admin_update_user_route_works(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.patch("/admin/users/2",
                                json={
                                    "full_name": "john smith"
                                },
                                headers=headers)

        self.assertEqual(response.status_code, 200, response.json())
        user2 = self.db.query(User).filter(User.id == 2).first()
        self.assertEqual(user2.full_name, "john smith")
        
    def test_admin_update_user_route_works_only_loggedin(self):
        response = client.patch("/admin/users/2",
                                json={
                                    "full_name": "gen. akbar"
                                })
        
        self.assertEqual(response.status_code, 401, response.json())
        user2 = self.db.query(User).filter(User.id == 2).first()
        self.assertEqual(user2.full_name, None, 
                         "Admin must be logged in.")

    def test_admin_update_user_route_works_only_with_admin_users(self):
        token = self.login_user(username="user2", password="user2")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.patch("/admin/users/2",
                                json={
                                    "full_name": "gen. akbar"
                                },
                                headers=headers)
        
        self.assertEqual(response.status_code, 401, response.json())
        user2 = self.db.query(User).filter(User.id == 2).first()
        self.assertEqual(user2.full_name, None,
                         "Normal users shouldn't be able to do this.")

    
    def test_admin_delete_user_route_works(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.delete("/admin/users/3",
                                headers=headers)
        
        self.assertEqual(response.status_code, 204)
        users_count = self.db.query(User).count()
        self.assertEqual(users_count, 2)

        response = client.delete("/admin/users/1")
        
        self.assertEqual(response.status_code, 401)
        users_count = self.db.query(User).count()
        self.assertEqual(users_count, 2)