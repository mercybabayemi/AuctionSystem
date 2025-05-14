from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

# Assuming your custom decorator is in a 'utils' directory at the same level as 'routers'
# If 'utils' is inside 'example', the path would be from ..utils.decorators import manual_jwt_required
from ..utils.decorators import manual_jwt_required 
from ..services.auction_service_impl import AuctionServiceImpl
from ..schemas.auction_schema import AuctionSchema
from src.config import Config
from ..models.user import User # For fetching user if needed, though id is often enough
from ..repositories.user_repository_impl import UserRepositoryImpl # To fetch user object
from ..exceptions.entity_not_found_exception import EntityNotFoundException
from ..exceptions.auction_error import AuctionError

auction_router = Blueprint('auction', __name__)
auction_service = AuctionServiceImpl()
auction_schema = AuctionSchema() # For single item serialization
auctions_schema = AuctionSchema(many=True) # For list serialization


@auction_router.route('/auction', methods=['POST'])
@manual_jwt_required
def create_auction(current_user_id):
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        image_file = request.files['image']
        # Ensure filename is safe
        if image_file.filename == '' or not AuctionServiceImpl._allowed_file(image_file.filename):
            return jsonify({"error": "Invalid or no selected image file"}), 400

        auction_data_form = request.form.to_dict()
        auction_data_form['seller_id'] = current_user_id # Set seller_id from authenticated user
        
        created_auction = auction_service.create_auction(auction_data_form, image_file)
        return jsonify(auction_schema.dump(created_auction)), 201
    except AuctionError as e: # Custom auction related errors from service layer
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating auction: {str(e)}")
        return jsonify({"error": "Failed to create auction due to an internal error."}), 500


@auction_router.route('/auction/<item_id>', methods=['GET'])
def get_auction(item_id):
    try:
        auction = auction_service.get_auction(item_id)
        if not auction:
            return jsonify({"error": "Auction not found"}), 404
        return jsonify(auction_schema.dump(auction)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@auction_router.route('/auction/<item_id>/bid', methods=['POST'])
@manual_jwt_required
def place_bid(current_user_id, item_id):
    data = request.get_json()
    if not data or 'bid_amount' not in data:
        return jsonify({"error": "Bid amount is required"}), 400

    try:
        bid_amount = data['bid_amount'] # Get bid_amount from the parsed data
        # Pass current_user_id (from decorator) as bidder_id
        updated_auction = auction_service.place_bid(item_id, current_user_id, float(bid_amount))
        # auction_service.place_bid should raise EntityNotFoundException or AuctionError on failure
        return jsonify(auction_schema.dump(updated_auction)), 200
    except EntityNotFoundException as e:
        current_app.logger.warning(f"Place bid failed for item {item_id}: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except AuctionError as e: # For errors like "bid too low", "auction closed" etc.
        current_app.logger.warning(f"Place bid business logic error for item {item_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400 
    except ValueError: # If float(bid_amount) fails
        return jsonify({"error": "Invalid bid amount format."}), 400
    except Exception as e:
        current_app.logger.error(f"Error placing bid on item {item_id}: {str(e)}")
        return jsonify({"error": "Failed to place bid due to an internal error."}), 500


@auction_router.route('/auctions', methods=['GET']) # Changed to /auctions for plurality
def list_items():
    try:
        items = auction_service.list_items()
        return jsonify(auctions_schema.dump(items)), 200 # Use schema for proper serialization
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auction_router.route('/auction/<item_id>', methods=['PUT'])
@manual_jwt_required
def edit_item(current_user_id, item_id):
    try:
        auction_data_form = request.form.to_dict()
        image_file = request.files.get('image') # Image is optional for update

        # Authorization: Check if the current_user is the seller of the auction item.
        # The auction_service.edit_item should ideally handle this logic internally for atomicity,
        # or this check should be extremely robust.
        # Fetching item first to check ownership before attempting edit:
        auction_to_edit = auction_service.get_auction_by_item_id(item_id) # Assuming this method exists
        if not auction_to_edit:
            return jsonify({"error": "Auction item not found"}), 404
        
        # Ensure seller_id from auction_to_edit is compared correctly with current_user_id
        # seller_id could be an object or a string ID. Adapt as necessary.
        # If auction_to_edit.seller_id is a User object: str(auction_to_edit.seller_id.id)
        # If auction_to_edit.seller_id is an ID string: str(auction_to_edit.seller_id)
        actual_seller_id = str(auction_to_edit.seller_id.id) if hasattr(auction_to_edit.seller_id, 'id') else str(auction_to_edit.seller_id)
        if actual_seller_id != current_user_id:
            current_app.logger.warning(f"User {current_user_id} attempt to edit auction {item_id} owned by {actual_seller_id}")
            return jsonify({"error": "Permission denied: You are not the seller of this item."}), 403

        # Now call the service to edit the item
        updated_auction = auction_service.edit_item(item_id, auction_data_form, image_file, current_user_id)
        return jsonify(auction_schema.dump(updated_auction)), 200
    except EntityNotFoundException as e: # If auction_service.edit_item itself raises this
        current_app.logger.warning(f"Edit auction failed, item {item_id} not found: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except AuctionError as e: # For other business logic errors from service
        current_app.logger.warning(f"Edit auction business logic error for item {item_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error editing auction item {item_id}: {str(e)}")
        return jsonify({"error": "Failed to edit auction item due to an internal error."}), 500
