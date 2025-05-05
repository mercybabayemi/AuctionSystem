from src.example.exceptions.entity_not_found_exception import EntityNotFoundException
from src.example.models.bid import Bid
from src.example.repositories.bid_repository import BidRepository


class BidRepositoryImpl(BidRepository):

    @staticmethod
    def save_bid(bid):
        bid.save()

    @staticmethod
    def find_bids_by_auction_id(auction_id):
        bids = Bid.objects(auction_id=auction_id).first()
        if not bids:
            raise EntityNotFoundException("Auction not found")
        return bids