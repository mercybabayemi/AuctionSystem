from datetime import datetime

from mongoengine import Document, StringField, DateTimeField, FloatField, ListField, ReferenceField, BooleanField


class Auction(Document):
    item_id = StringField(required=True, unique=True)
    seller_id = ReferenceField('User', required=True)
    starting_bid = FloatField(required=True)
    bids = ListField(ReferenceField('Bid'), default=list)
    item_description = StringField(required=True)
    item_title = StringField(required=True)
    image_filename = StringField()  # Stores the name of the uploaded image file
    start_time = DateTimeField(default=datetime.utcnow)
    end_time = DateTimeField()
    is_approved = BooleanField(default=False)

    def to_dict(self):
        return {
            'item_id': self.item_id,
            'seller_id': self.seller_id,
            'starting_bid': self.starting_bid,
            'bids': self.bids,
            'item_description': self.item_description,
            'item_title': self.item_title,
            'image_filename': self.image_filename,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time,
            'is_approved': self.is_approved
        }

    meta = {'collection': 'auction'}