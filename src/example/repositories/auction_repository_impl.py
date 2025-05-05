from example.exceptions.entity_not_found_exception import EntityNotFoundException
from example.models.auction import Auction
from src.example.repositories.auction_repository import AuctionRepository


class AuctionRepositoryImpl(AuctionRepository):
    @staticmethod
    def find_auction_by_id(item_id):
        auction = Auction.objects(item_id=item_id).first()
        if not auction:
            raise EntityNotFoundException("Auction not found")
        return auction

    @staticmethod
    def save_auction(auction):
        auction.save()