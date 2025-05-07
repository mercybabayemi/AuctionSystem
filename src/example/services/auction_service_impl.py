import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

from werkzeug.exceptions import HTTPException

from example.exceptions.auth_error import AuthError
from example.exceptions.entity_not_found_exception import EntityNotFoundException
from example.exceptions.validation_error import ValidationError
from example.models.bid import Bid
from example.repositories.bid_repository import BidRepository
from src.example.models.auction import Auction
from src.example.models.user import User
from src.example.repositories.auction_repository import AuctionRepository
from src.example.schemas.auction_schema import AuctionSchema
from src.example.services.auction_service import AuctionService
from src.extensions import broadcast_new_bid # Import the broadcast function


class AuctionServiceImpl(AuctionService):
    @staticmethod
    def _allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

    @staticmethod
    def _save_auction_image(image_file):
        if image_file and AuctionServiceImpl._allowed_file(image_file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{image_file.filename}")
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            return filename
        return None

    @staticmethod
    def create_auction(auction_data, image_file=None):
        # user = User() # This line seems unused, consider removing or implementing user association
        auction_schema = AuctionSchema()
        # Marshmallow loads data, but file is handled separately
        validated_data = auction_schema.load(auction_data)

        # Create Auction object directly from validated data
        auction = Auction(**validated_data)
        
        if image_file:
            image_filename = AuctionServiceImpl._save_auction_image(image_file)
            if image_filename:
                auction.image_filename = image_filename
            else:
                # Optional: Raise an error or return a specific response if image saving fails
                pass 

        # Assuming seller_id is part of auction_data and is a valid User ID string
        # If seller_id needs to be the current authenticated user, adjust logic here
        # For now, assuming auction_data['seller_id'] is a User document or its ID
        # If it's an ID, it needs to be fetched: auction.seller_id = User.objects.get(id=validated_data['seller_id'])
        # This depends on how seller_id is passed and if User model is fully integrated here.

        AuctionRepository.save_auction(auction)
        return auction # Return the created auction object

    @staticmethod
    def get_auction(item_id):
        return AuctionRepository.find_auction_by_id(item_id)

    @staticmethod
    def list_items():
        return Auction.objects.all()

    @staticmethod
    def edit_item(item_id: str, data: dict, image_file=None) -> None:
        auction_schema = AuctionSchema(partial=True) # Allow partial updates
        auction_data = auction_schema.load(data)
        auction = AuctionRepository.find_auction_by_id(item_id)
        if not auction:
            raise EntityNotFoundException("Auction not found.")

        for key, value in auction_data.items():
            setattr(auction, key, value)

        if image_file:
            # Optionally, delete the old image if replacing
            # if auction.image_filename:
            #     old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], auction.image_filename)
            #     if os.path.exists(old_image_path):
            #         os.remove(old_image_path)
            
            image_filename = AuctionServiceImpl._save_auction_image(image_file)
            if image_filename:
                auction.image_filename = image_filename
            else:
                # Optional: Handle image saving failure
                pass

        auction.save()

    @staticmethod
    def approve_item(item_id):
        auction = AuctionRepository.find_auction_by_id(item_id)
        auction.is_approved = True
        auction.save()

    @staticmethod
    def place_bid(auction_id, user, bid_amount):
        auction = AuctionRepository.find_auction_by_id(auction_id)
        if bid_amount <= auction.starting_bid:
            raise ValidationError("Bid must be higher than the starting bid.")
        bid = Bid(auction_id=auction, bidder_id=user, bid_amount=bid_amount)
        BidRepository.save_bid(bid)

        # Broadcast the new bid via WebSocket
        bid_data = {
            'auction_id': str(auction.id), # Ensure ID is a string for JSON/JS
            'new_price': float(bid.bid_amount), # Ensure price is a float
            # Add other relevant data if needed (e.g., bidder name, time left)
        }
        broadcast_new_bid(auction_id=str(auction.id), bid_data=bid_data)

    @staticmethod
    def view_bid_history(auction_id):
        return BidRepository.find_bids_by_auction_id(auction_id)