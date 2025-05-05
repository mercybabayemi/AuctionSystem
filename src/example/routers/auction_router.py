from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_current_user

from ..services.auction_service_impl import AuctionServiceImpl

auction_router = Blueprint('auction', __name__)
auction_service = AuctionServiceImpl()

@auction_router.route('/auction', methods=['POST'])
def create_auction():
    try:
        auction_data = request.get_json()
        auction_service.create_auction(auction_data)
        return jsonify({"message": "Auction created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auction_router.route('/auction/<item_id>', methods=['GET'])
def get_auction(item_id):
    try:
        auction = auction_service.get_auction(item_id)
        return jsonify(auction), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@auction_router.route('/auction/<item_id>/bid', methods=['POST'])
def place_bid(item_id):
    try:
        user = get_current_user()
        bid_amount = request.json.get('bid_amount')
        auction_service.place_bid(item_id, user, bid_amount)
        return jsonify({"message": "Bid placed successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auction_router.route('/auction', methods=['GET'])
def list_items():
    try:
        items = auction_service.list_items()
        return jsonify(items), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auction_router.route('/auction/<item_id>', methods=['PUT'])
def edit_item(item_id):
    try:
        data = request.get_json()
        auction_service.edit_item(item_id, **data)
        return jsonify({"message": "Item updated successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

