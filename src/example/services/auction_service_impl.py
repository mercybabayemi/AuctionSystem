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


class AuctionServiceImpl(AuctionService):
    @staticmethod
    def create_auction(auction_data):
        user = User()
        auction_schema = AuctionSchema()
        auction = auction_schema.load(auction_data)
        AuctionRepository.save_auction(auction)

    @staticmethod
    def get_auction(item_id):
        return AuctionRepository.find_auction_by_id(item_id)

    @staticmethod
    def list_items():
        return Auction.objects.all()

    @staticmethod
    def edit_item(item_id: str, **data: dict) -> None:
        auction_schema = AuctionSchema()
        auction_data = auction_schema.load(data)
        auction = AuctionRepository.find_auction_by_id(item_id)
        if not auction:
            raise EntityNotFoundException("Auction not found.")
        for key, value in auction_data.items():
            setattr(auction, key, value)
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

    @staticmethod
    def view_bid_history(auction_id):
        return BidRepository.find_bids_by_auction_id(auction_id)