import json
from io import BytesIO
import os
import uuid # For generating unique item_ids

from test.base_test import BaseTestCase
from src.example.models.user import User
from src.example.models.auction import Auction
from src.config import Config # To get UPLOAD_FOLDER for cleanup

class TestAuctionRoutes(BaseTestCase):

    def _create_auction_payload(self, item_id=None, item_title="Test Item", item_description="A great test item", starting_bid=10.0):
        return {
            'item_id': item_id if item_id else str(uuid.uuid4()), # Ensure unique item_id
            'item_title': item_title,
            'item_description': item_description,
            'starting_bid': starting_bid
        }

    def _create_dummy_image(self, filename="test_image.png", content_type='image/png'):
        return (BytesIO(b"someinitialimagedata"), filename, content_type)

    def tearDown(self):
        """Clean up uploaded test files after each auction test if any."""
        super().tearDown() # Call parent tearDown for general cleanup
        # Clean up any files created in UPLOAD_FOLDER during tests
        upload_folder = Config.UPLOAD_FOLDER
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.startswith("test_") or "testauction" in filename: # Be specific to avoid deleting wanted files
                    try:
                        os.remove(os.path.join(upload_folder, filename))
                    except OSError as e:
                        print(f"Error deleting test file {filename}: {e}")

    # --- Test Create Auction ---
    def test_create_auction_success(self):
        user_headers = self._get_auth_headers(username="seller")
        auction_data = self._create_auction_payload(item_id="testauction001")
        image_file = self._create_dummy_image(filename="test_image_create.png")
        
        data_with_image = auction_data.copy()
        data_with_image['image'] = image_file

        response = self.client.post('/api/auction', headers=user_headers, 
                                    data=data_with_image, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 201)
        self.assertIn("item_id", response.json)
        self.assertEqual(response.json['item_id'], "testauction001")
        self.assertIn('image_filename', response.json) # Check if image_filename is returned
        self.assertIsNotNone(response.json['image_filename'])
        # Verify auction in DB
        auction = Auction.objects(item_id="testauction001").first()
        self.assertIsNotNone(auction)
        self.assertEqual(auction.item_title, auction_data['item_title'])
        self.assertIsNotNone(auction.image_filename)
        # Check if file exists in upload folder
        self.assertTrue(os.path.exists(os.path.join(Config.UPLOAD_FOLDER, auction.image_filename)))

    def test_create_auction_no_image(self):
        user_headers = self._get_auth_headers(username="seller_no_image")
        auction_data = self._create_auction_payload()
        response = self.client.post('/api/auction', headers=user_headers, 
                                    data=auction_data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn("No image file provided", response.json.get('error', ''))

    def test_create_auction_invalid_file_type(self):
        user_headers = self._get_auth_headers(username="seller_bad_file")
        auction_data = self._create_auction_payload(item_id="testauction_badfile")
        invalid_image = (BytesIO(b"notanimage"), "test.txt", "text/plain")
        data_with_image = auction_data.copy()
        data_with_image['image'] = invalid_image
        response = self.client.post('/api/auction', headers=user_headers, 
                                    data=data_with_image, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid or no selected image file", response.json.get('error', ''))

    def test_create_auction_no_token(self):
        auction_data = self._create_auction_payload()
        image_file = self._create_dummy_image()
        data_with_image = auction_data.copy()
        data_with_image['image'] = image_file
        response = self.client.post('/api/auction', data=data_with_image, 
                                    content_type='multipart/form-data', headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 401) # No auth

    # --- Test Get Auction --- 
    def test_get_auction_success(self):
        seller = self._register_user(username="auction_owner")
        auction = Auction(item_id="auction123", seller_id=seller, item_title="Readable Item", item_description="Desc", starting_bid=50).save()
        response = self.client.get(f'/api/auction/{auction.item_id}', headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['item_id'], auction.item_id)
        self.assertEqual(response.json['item_title'], "Readable Item")

    def test_get_auction_not_found(self):
        response = self.client.get('/api/auction/nonexistentitem', headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json.get("error", "").lower())

    # --- Test List Auctions ---
    def test_list_auctions_success(self):
        seller = self._register_user(username="list_seller")
        Auction(item_id="itemA", seller_id=seller, item_title="Item A", item_description="A", starting_bid=10).save()
        Auction(item_id="itemB", seller_id=seller, item_title="Item B", item_description="B", starting_bid=20).save()
        response = self.client.get('/api/auctions', headers=self._get_no_auth_headers()) # Endpoint is /auctions
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertEqual(len(response.json), 2)
        item_ids_in_response = {item['item_id'] for item in response.json}
        self.assertIn("itemA", item_ids_in_response)
        self.assertIn("itemB", item_ids_in_response)

    # --- Test Place Bid ---
    def test_place_bid_success(self):
        seller = self._register_user(username="bid_seller")
        auction = Auction(item_id="biditem001", seller_id=seller, item_title="Biddable", item_description="Test", starting_bid=10.0).save()
        bidder_headers = self._get_auth_headers(username="bidder")
        bid_payload = {"bid_amount": 15.0}
        response = self.client.post(f'/api/auction/{auction.item_id}/bid', headers=bidder_headers, data=json.dumps(bid_payload))
        self.assertEqual(response.status_code, 200)
        # Assuming place_bid returns the updated auction with the new bid reflected somehow (e.g., in a bids list or highest_bid field)
        # This assertion will depend on how your AuctionSchema serializes bid information.
        # For now, we just check success and perhaps the item_id.
        self.assertEqual(response.json['item_id'], auction.item_id)
        # You might want to assert that auction.current_bid (or similar) is updated in the DB.

    def test_place_bid_too_low(self):
        seller = self._register_user(username="bid_seller_low")
        auction = Auction(item_id="biditem002", seller_id=seller, item_title="Biddable Low", item_description="Test", starting_bid=20.0).save()
        bidder_headers = self._get_auth_headers(username="lowbidder")
        bid_payload = {"bid_amount": 5.0} # Lower than starting_bid
        response = self.client.post(f'/api/auction/{auction.item_id}/bid', headers=bidder_headers, data=json.dumps(bid_payload))
        self.assertEqual(response.status_code, 400) # AuctionError from service
        self.assertIn("error", response.json)
        self.assertIn("must be higher", response.json['error'].lower())

    def test_place_bid_missing_amount(self):
        seller = self._register_user(username="bid_seller_nobid")
        auction = Auction(item_id="biditem003", seller_id=seller, item_title="Biddable No Bid", item_description="Test", starting_bid=10.0).save()
        bidder_headers = self._get_auth_headers(username="nobidder")
        response = self.client.post(f'/api/auction/{auction.item_id}/bid', headers=bidder_headers, data=json.dumps({})) # Empty payload
        self.assertEqual(response.status_code, 400)
        self.assertIn("Bid amount is required", response.json['error'])

    def test_place_bid_auction_not_found(self):
        bidder_headers = self._get_auth_headers(username="ghostbidder")
        bid_payload = {"bid_amount": 100.0}
        response = self.client.post('/api/auction/nonexistentauction/bid', headers=bidder_headers, data=json.dumps(bid_payload))
        self.assertEqual(response.status_code, 404) # EntityNotFoundException from service
        self.assertIn("not found", response.json.get("error", "").lower())

    def test_place_bid_no_token(self):
        bid_payload = {"bid_amount": 20.0}
        response = self.client.post('/api/auction/someitem/bid', data=json.dumps(bid_payload), headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 401)

    # --- Test Edit Auction ---
    def test_edit_auction_success_by_owner(self):
        owner_headers = self._get_auth_headers(username="auctionowner")
        owner_user = User.objects(username="auctionowner").first()
        auction = Auction(item_id="editme001", seller_id=owner_user, item_title="Original Title", item_description="Original Desc", starting_bid=25.0, image_filename="original.jpg").save()
        
        edit_payload = {"item_title": "Updated Title", "item_description": "Updated Desc"}
        # Image update is optional, so not including it here for this test case
        response = self.client.put(f'/api/auction/{auction.item_id}', headers=owner_headers, 
                                   data=edit_payload, content_type='application/x-www-form-urlencoded') # If using forms for PUT
                                   # If using JSON for PUT: data=json.dumps(edit_payload), content_type='application/json'
                                   # Matching auction_router.py, it uses request.form.to_dict(), so form-urlencoded is more appropriate if image isn't sent.
                                   # If image can also be sent, it has to be multipart/form-data
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['item_title'], "Updated Title")
        updated_auction = Auction.objects(item_id="editme001").first()
        self.assertEqual(updated_auction.item_description, "Updated Desc")

    def test_edit_auction_with_image_by_owner(self):
        owner_headers = self._get_auth_headers(username="imageeditor")
        owner_user = User.objects(username="imageeditor").first()
        auction = Auction(item_id="editimage001", seller_id=owner_user, item_title="Image Edit", image_filename="old_image.png", starting_bid=30).save()
        
        edit_payload_form = {"item_title": "New Image Title"}
        new_image = self._create_dummy_image(filename="test_new_image.jpg")
        edit_payload_form['image'] = new_image

        response = self.client.put(f'/api/auction/{auction.item_id}', headers=owner_headers, 
                                   data=edit_payload_form, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['item_title'], "New Image Title")
        self.assertNotEqual(response.json['image_filename'], "old_image.png")
        self.assertTrue(os.path.exists(os.path.join(Config.UPLOAD_FOLDER, response.json['image_filename'])))


    def test_edit_auction_forbidden_not_owner(self):
        owner = self._register_user(username="actualowner")
        auction = Auction(item_id="editme002", seller_id=owner, item_title="Not Yours", starting_bid=10).save()
        attacker_headers = self._get_auth_headers(username="attacker")
        edit_payload = {"item_title": "Trying to edit"}
        response = self.client.put(f'/api/auction/{auction.item_id}', headers=attacker_headers, 
                                   data=edit_payload, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 403) # Permission denied
        self.assertIn("Permission denied", response.json['error'])

    def test_edit_auction_not_found(self):
        owner_headers = self._get_auth_headers(username="editor_no_item")
        edit_payload = {"item_title": "Ghost Edit"}
        response = self.client.put('/api/auction/nonexistentitemtoedit', headers=owner_headers, 
                                   data=edit_payload, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 404)

    def test_edit_auction_no_token(self):
        edit_payload = {"item_title": "No Token Edit"}
        response = self.client.put('/api/auction/someitemtoedit_notoken', 
                                   data=edit_payload, content_type='application/x-www-form-urlencoded', headers=self._get_no_auth_headers())
        self.assertEqual(response.status_code, 401)

# To run: python -m unittest discover -s test
# Or: python test/test_auction_routes.py (if __main__ block is added)
