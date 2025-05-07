from mongoengine import Document, StringField, DictField, DateTimeField, BooleanField, IntField
from datetime import datetime

class User(Document):
    user_id = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    username = StringField(required=True, unique=True)
    roles = DictField(default={
        'is_super_admin': False,
        'is_admin': False,
        'is_buyer': True,
        'is_seller': True
    })
    created_at = DateTimeField(default=datetime.utcnow)
    is_blocked = BooleanField(default=False)
    token_version = IntField(default=0)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email': self.email,
            'password': self.password,
            'username': self.username,
            'roles': self.roles,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_blocked': self.is_blocked
        }

    meta = {'collection': 'user'}
