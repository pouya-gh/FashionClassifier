from fastapi.testclient import TestClient
from app.routes.admin.apikeys import router
from app.database.models import User, APIKey
from fastapi import FastAPI

from app.utils.auth import hash_password, authenticate_user, create_access_token
from app.utils.testing.testcase import MyTestCase
from app.utils.testing.database import get_test_db

from datetime import datetime, timedelta



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

    def test_admin_get_apikey_details_route_works(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/admin/apikeys/1",
                              headers=headers)
        
        self.assertEqual(response.status_code, 200, response.json())

        response = client.get("/admin/apikeys/1")
        
        self.assertEqual(response.status_code, 401, "This shouldn't work if not logged in.")

    def test_admin_update_apikey_route_works(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.patch("/admin/apikeys/2",
                                json={
                                    "key": "brand_new_key"
                                },
                                headers=headers)

        self.assertEqual(response.status_code, 200, response.json())
        api_key = self.db.query(APIKey).filter(APIKey.id == 2).first()
        self.assertEqual(api_key.key, "brand_new_key")
        
    def test_admin_update_apikey_route_works_only_loggedin(self):
        response = client.patch("/admin/apikeys/2",
                                json={
                                    "key": "unauthorized_key"
                                })
        
        self.assertEqual(response.status_code, 401, response.json())
        api_key = self.db.query(APIKey).filter(APIKey.id == 2).first()
        self.assertEqual(api_key.key, "test_key_2", 
                         "Admin must be logged in.")

    def test_admin_update_apikey_route_works_only_with_admin_users(self):
        token = self.login_user(username="user2", password="user2")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.patch("/admin/apikeys/2",
                                json={
                                    "key": "unauthorized_key"
                                },
                                headers=headers)
        
        self.assertEqual(response.status_code, 401, response.json())
        api_key = self.db.query(APIKey).filter(APIKey.id == 2).first()
        self.assertEqual(api_key.key, "test_key_2",
                         "Normal users shouldn't be able to do this.")

    
    def test_admin_delete_apikey_route_works(self):
        token = self.login_user(username="user1", password="user1")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.delete("/admin/apikeys/3",
                                 headers=headers)
        
        self.assertEqual(response.status_code, 204)
        apikeys_count = self.db.query(APIKey).count()
        self.assertEqual(apikeys_count, 2)

        response = client.delete("/admin/apikeys/1")
        
        self.assertEqual(response.status_code, 401)
        apikeys_count = self.db.query(APIKey).count()
        self.assertEqual(apikeys_count, 2)