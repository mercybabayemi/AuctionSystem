import unittest
import json
import os
from mongoengine import connect, disconnect, get_connection

# Import your Flask app instance and models
from src.app import app as flask_app 
from src.example.models.user import User
from src.example.models.auction import Auction
# from src.example.models.bid import Bid # Uncomment if you have this model

from src.example.services.user_service_impl import UserServiceImpl
from src.example.utils.token_util import generate_token, decode_token # Added decode_token for one test case
from src.example.exceptions.auth_error import AuthError # For testing expired/invalid token

class BaseTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up for all tests in this class."""
        cls.app = flask_app
        cls.app.config['TESTING'] = True
        cls.app.config['JWT_SECRET_KEY'] = 'super-secret-test-jwt' # Default for token generation
        cls.app.config['SECRET_KEY'] = 'super-secret-test-flask'
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.app.config['JWT_EXPIRATION_SECONDS'] = 3600 # Default expiration

        # Disconnect any existing default connection
        try:
            disconnect(alias='default')
        except Exception:
            pass

        cls.test_db_name = os.environ.get("MONGO_TEST_DB", "auction_unittest_db")
        connect(db=cls.test_db_name, alias='default')
        cls.app.config['MONGODB_DB'] = cls.test_db_name
        
        cls.client = cls.app.test_client()
        cls.user_service = UserServiceImpl()

    @classmethod
    def tearDownClass(cls):
        """Tear down after all tests in this class."""
        try:
            connection = get_connection(alias='default')
            connection.drop_database(cls.test_db_name)
        except Exception as e:
            print(f"Could not drop test database {cls.test_db_name}: {e}")
        finally:
            disconnect(alias='default')

    def setUp(self):
        """Set up before each test method."""
        # Clean up collections before each test
        User.objects.delete()
        Auction.objects.delete()
        # if 'Bid' in globals() and hasattr(Bid, 'objects'):
        #     Bid.objects.delete()

    def tearDown(self):
        """Tear down after each test method."""
        # Reset JWT_EXPIRATION_SECONDS to default if changed in a test
        self.app.config['JWT_EXPIRATION_SECONDS'] = 3600

    # Helper methods
    def _create_user_payload(self, username="testuser", email_suffix="@example.com", password="password123", full_name="Test User", is_admin=False, is_super_admin=False):
        email = f"{username}{email_suffix}"
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "roles": {}
        }
        if is_admin:
            payload["roles"]["is_admin"] = True
        if is_super_admin: # Super admins are also admins
            payload["roles"]["is_super_admin"] = True
            payload["roles"]["is_admin"] = True
        return payload

    def _register_user(self, username="testuser", email_suffix="@example.com", password="password123", full_name="Test User", is_admin=False, is_super_admin=False):
        payload = self._create_user_payload(username, email_suffix, password, full_name, is_admin, is_super_admin)
        # Assuming register_user returns a dictionary or the created user object that includes the id
        created_entity = self.user_service.register_user(payload) 
        user_obj = User.objects(username=payload["username"]).first()
        if not user_obj:
            self.fail(f"Test user {payload['username']} not found after registration attempt.")
        return user_obj

    def _get_auth_headers(self, username="testuser", is_admin=False, is_super_admin=False):
        user = self._register_user(username=username, is_admin=is_admin, is_super_admin=is_super_admin)
        token = generate_token(user) 
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _get_no_auth_headers(self):
        return {'Content-Type': 'application/json'}

    def _get_expired_token_headers(self, username="expireduser"):
        user = self._register_user(username=username)
        # Temporarily set token expiration to a very short time
        original_expiration = self.app.config['JWT_EXPIRATION_SECONDS']
        self.app.config['JWT_EXPIRATION_SECONDS'] = 1 # 1 second
        token = generate_token(user)
        # time.sleep(2) # Wait for token to expire - this might make tests slow, alternative below
        self.app.config['JWT_EXPIRATION_SECONDS'] = original_expiration # Reset for other tests
        # Instead of sleeping, we can rely on the decode_token to raise AuthError for expired token
        # This requires that manual_jwt_required decorator correctly handles AuthError from decode_token
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }, token # Return token too for manual check if needed

# To allow running this file directly for discovery by some runners, though typically not needed with `python -m unittest discover`
# if __name__ == '__main__':
#     unittest.main()
