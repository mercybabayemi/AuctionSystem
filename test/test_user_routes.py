# test/test_user_routes.py
import json
from io import BytesIO # For file uploads

from test.base_test import BaseTestCase # Import the BaseTestCase
from src.example.models.user import User
from src.example.models.auction import Auction # For tests that might interact with auctions tied to users

class TestUserRoutes(BaseTestCase):

    # --- Test User Registration ---
    def test_register_user_success(self):
        payload = self._create_user_payload(username="newbie", email_suffix="@test.com")
        response = self.client.post('/api/register', data=json.dumps(payload), headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], "User registered successfully")
        user = User.objects(username="newbie").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "newbie@test.com")

    def test_register_user_duplicate_username(self):
        self._register_user(username="existinguser") # First, register a user
        payload = self._create_user_payload(username="existinguser", email_suffix="@another.com")
        response = self.client.post('/api/register', data=json.dumps(payload), headers=self._get_no_auth_headers())
        # Assuming your service raises an exception that results in a 400 or 409 (Conflict)
        # Update status_code based on actual implementation for duplicate user error
        self.assertIn(response.status_code, [400, 409, 422]) 
        self.assertIn("error", response.json)
        self.assertIn("already exists", response.json['error'].lower())

    def test_register_user_missing_username(self):
        payload = self._create_user_payload()
        del payload['username']
        response = self.client.post('/api/register', data=json.dumps(payload), headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 400) # Or 422 if using Marshmallow validation that raises specific error
        self.assertIn("error", response.json)

    def test_register_user_missing_password(self):
        payload = self._create_user_payload()
        del payload['password']
        response = self.client.post('/api/register', data=json.dumps(payload), headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 400) # Or 422
        self.assertIn("error", response.json)

    # --- Test User Login ---
    def test_login_user_success(self):
        self._register_user(username="loginuser", password="greatpassword")
        login_data = {"username": "loginuser", "password": "greatpassword"}
        response = self.client.post('/api/login', data=json.dumps(login_data), headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json)

    def test_login_user_wrong_password(self):
        self._register_user(username="loginuser2", password="correctpassword")
        login_data = {"username": "loginuser2", "password": "wrongpassword"}
        response = self.client.post('/api/login', data=json.dumps(login_data), headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)
        self.assertEqual(response.json['error'], "Invalid credentials")

    def test_login_user_nonexistent_user(self):
        login_data = {"username": "iamghost", "password": "anypassword"}
        response = self.client.post('/api/login', data=json.dumps(login_data), headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)
        self.assertEqual(response.json['error'], "Invalid credentials")

    # --- Test Create Admin (Protected Route) ---
    def test_create_admin_success_by_superadmin(self):
        super_admin_headers = self._get_auth_headers(username="superboss", is_super_admin=True)
        admin_to_create_payload = self._create_user_payload(username="newchief", email_suffix="@admin.com")
        response = self.client.post('/api/create_admin', headers=super_admin_headers, data=json.dumps(admin_to_create_payload))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], "Admin user created successfully")
        self.assertIn("user_id", response.json)
        new_admin_user = User.objects(username="newchief").first()
        self.assertIsNotNone(new_admin_user)
        self.assertTrue(new_admin_user.roles.get('is_admin'))

    def test_create_admin_denied_for_regular_admin(self):
        admin_headers = self._get_auth_headers(username="justadmin", is_admin=True, is_super_admin=False)
        admin_to_create_payload = self._create_user_payload(username="anotheradmin")
        response = self.client.post('/api/create_admin', headers=admin_headers, data=json.dumps(admin_to_create_payload))
        self.assertEqual(response.status_code, 403)
        self.assertIn("Permission denied", response.json['error'])

    def test_create_admin_denied_for_regular_user(self):
        user_headers = self._get_auth_headers(username="justauser")
        admin_to_create_payload = self._create_user_payload(username="wannabeadmin")
        response = self.client.post('/api/create_admin', headers=user_headers, data=json.dumps(admin_to_create_payload))
        self.assertEqual(response.status_code, 403)
        self.assertIn("Permission denied", response.json['error'])

    def test_create_admin_no_token(self):
        admin_to_create_payload = self._create_user_payload(username="secretadmin")
        response = self.client.post('/api/create_admin', data=json.dumps(admin_to_create_payload), headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authorization header is missing", response.json['error'])
        
    def test_create_admin_expired_token(self):
        expired_headers, _ = self._get_expired_token_headers("userWithExpiredTokenForAdminCreate")
        admin_to_create_payload = self._create_user_payload(username="someadmin")
        response = self.client.post('/api/create_admin', headers=expired_headers, data=json.dumps(admin_to_create_payload))
        self.assertEqual(response.status_code, 401) 
        self.assertIn("Token has expired", response.json.get("error", ""))

    def test_create_admin_invalid_token(self):
        headers = {'Authorization': 'Bearer invalidtokenstring', 'Content-Type': 'application/json'}
        admin_to_create_payload = self._create_user_payload(username="anothersecretadmin")
        response = self.client.post('/api/create_admin', headers=headers, data=json.dumps(admin_to_create_payload))
        self.assertEqual(response.status_code, 401) 
        self.assertIn("Invalid token", response.json.get("error", "").lower())

    # --- Test Block User (Protected Route) ---
    def test_block_user_success_by_admin(self):
        admin_headers = self._get_auth_headers(username="blockadmin", is_admin=True)
        user_to_block = self._register_user(username="tobeblocked")
        response = self.client.post(f'/api/user/{user_to_block.user_id}/block', headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], "User blocked successfully.")
        blocked_user = User.objects(id=user_to_block.id).first()
        self.assertIsNotNone(blocked_user)
        self.assertTrue(blocked_user.is_blocked) # Assumes User model has 'is_blocked' field

    def test_block_user_success_by_superadmin(self):
        super_admin_headers = self._get_auth_headers(username="blocksuperadmin", is_super_admin=True)
        user_to_block = self._register_user(username="tobeblockedsuper")
        response = self.client.post(f'/api/user/{user_to_block.user_id}/block', headers=super_admin_headers)
        self.assertEqual(response.status_code, 200)
        blocked_user = User.objects(id=user_to_block.id).first()
        self.assertTrue(blocked_user.is_blocked)

    def test_block_user_denied_for_regular_user(self):
        user_headers = self._get_auth_headers(username="cantblockuser")
        user_to_block = self._register_user(username="nottoblocked")
        response = self.client.post(f'/api/user/{user_to_block.user_id}/block', headers=user_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Permission denied", response.json['error'])

    def test_block_user_no_token(self):
        user_to_block = self._register_user(username="blockmenotoken")
        response = self.client.post(f'/api/user/{user_to_block.user_id}/block', headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authorization header is missing", response.json['error'])

    def test_block_nonexistent_user(self):
        admin_headers = self._get_auth_headers(username="adminblocksnone", is_admin=True)
        non_existent_user_id = "60c72b9f9b1e8b3b3c8e4a5b" # A plausible but likely non-existent ObjectId string
        response = self.client.post(f'/api/user/{non_existent_user_id}/block', headers=admin_headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json.get("error", "").lower())
        
    def test_block_user_with_expired_token(self):
        expired_headers, _ = self._get_expired_token_headers("expUserBlock")
        user_to_block = self._register_user(username="someUserToBlockExpToken")
        response = self.client.post(f'/api/user/{user_to_block.user_id}/block', headers=expired_headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Token has expired", response.json.get("error", ""))

    def test_block_user_with_invalid_token(self):
        headers = {'Authorization': 'Bearer invalidtokenstringagain', 'Content-Type': 'application/json'}
        user_to_block = self._register_user(username="someUserToBlockInvalidToken")
        response = self.client.post(f'/api/user/{user_to_block.user_id}/block', headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid token", response.json.get("error", "").lower())


# To run tests from the command line (from the root of your project):
# python -m unittest discover -s test
# Or, if you add the following to the end of this file:
# if __name__ == '__main__':
#     unittest.main()
# Then you can run this file directly: python test/test_user_routes.py
