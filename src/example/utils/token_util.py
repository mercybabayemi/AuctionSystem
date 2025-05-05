from jwt import PyJWTError
import jwt
from datetime import datetime, timezone, timedelta
from flask import current_app

from example.models.user import User
from src.example.exceptions.auth_error import AuthError


def generate_token(user):
    try:
        payload = {
            'sub': str(user.user_id),
            'user_id': str(user.user_id),
            'version': user.token_version,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=current_app.config['JWT_EXPIRATION_SECONDS'])
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    except Exception as e:
        return f"Token generation failed: {str(e)}"


def decode_token(token):
    try:
        token = token.replace('Bearer ', '').strip()

        token += '=' * (4 - len(token) % 4)
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256'],
            options={'verify_exp': True}
        )

        user = User.objects.get(
            __raw__={'$or': [
                {'_id': payload.get('sub')},
                {'user_id': payload.get('user_id')}
            ]}
        )

        if payload['version'] != user.token_version:
            raise AuthError("Token invalidated")

        return str(user.user_id)
    except PyJWTError as e:
        current_app.logger.error(f"JWT Error: {str(e)}")
        raise AuthError("Invalid or expired token")
    except DoesNotExist:
        raise AuthError("User not found")