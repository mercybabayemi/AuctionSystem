from mongoengine import Document, FloatField, ReferenceField, StringField


class Bid(Document):
    auction_id = ReferenceField('Auction', required=True)
    bidder_id = ReferenceField('User', required=True)
    bid_amount = FloatField(required=True)

    meta = {'collection': 'bid'}