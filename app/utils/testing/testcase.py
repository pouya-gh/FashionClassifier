from unittest import TestCase
from sqlalchemy.orm import Session

from app.database.db import Base, engine, get_db

class MyTestCase(TestCase):
    @classmethod
    def setTestData(cls):
        raise NotImplemented("""test data is not set. 
                             you must at least set \"app\" variable for test case to work.""")

    @classmethod
    def setUpClass(cls):
        cls.connection = engine.connect()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        cls.setTestData() # cls.app must be set here.
        cls.db = Session(bind=cls.connection)
        cls.app.dependency_overrides[get_db] = lambda: cls.db
    
    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)

        cls.app.dependency_overrides.clear()

        cls.db.close()
        cls.connection.close()
    
    def setUp(self):
        self.transaction = self.connection.begin()

    def tearDown(self):
        self.transaction.rollback()