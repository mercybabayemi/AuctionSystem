from marshmallow import Schema, fields
from flask import url_for

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
    image_filename = fields.Str(dump_only=True)  # We'll get the image via file upload, not this field
    image_url = fields.Method("get_image_url", dump_only=True)

    def get_image_url(self, obj):
        if obj.image_filename:
            # Assuming you will have a static endpoint for uploaded images
            return url_for('static', filename=f'uploads/auction_images/{obj.image_filename}', _external=True)
        return None