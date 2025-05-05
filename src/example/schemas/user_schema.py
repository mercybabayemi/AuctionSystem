from marshmallow import Schema, fields, post_load


class UserSchema(Schema):
    user_id = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    username = fields.Str(required=True)
    roles = fields.Dict(keys=fields.Str(), values=fields.Bool())
    created_at = fields.DateTime()
    is_blocked = fields.Bool()