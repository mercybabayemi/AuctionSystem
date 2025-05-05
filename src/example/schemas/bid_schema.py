from marshmallow import Schema, fields, post_load


class BidSchema(Schema):
    auction_id = fields.Str(required=True)
    bidder_id = fields.Str(required=True)
    bid_amount = fields.Float(required=True)