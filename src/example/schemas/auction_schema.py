from marshmallow import Schema, fields

from example.schemas.bid_schema import BidSchema


class AuctionSchema(Schema):
    item_id = fields.Str(required=True)
    seller_id = fields.Str(required=True)
    starting_bid = fields.Float(required=True)
    bids = fields.List(fields.Nested(BidSchema()), default=list)
    item_description = fields.Str(required=True)
    item_title = fields.Str(required=True)
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    is_approved = fields.Bool()