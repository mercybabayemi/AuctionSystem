from mongoengine import DoesNotExist

from ..models.user import User
from ..exceptions.entity_not_found_exception import EntityNotFoundException
from ..repositories.user_repository import UserRepository

class UserRepositoryImpl(UserRepository):
    @staticmethod
    def find_user_by_id(user_id):
        user = User.objects(user_id=user_id).first()
        if not user:
            raise EntityNotFoundException("User not found")
        return user

    @staticmethod
    def save_user(user):
        user.save()

    @staticmethod
    def find_user_by_username(username):
        user = User.objects(username=username).first()
        if not user:
            raise EntityNotFoundException("User not found")
        return user

    @staticmethod
    def count():
        count = User.objects.count()
        return count

    @staticmethod
    def invalidate_token(user_id):
        """Add token to blacklist or update user token version"""
        user = User.objects.get(user_id=user_id)
        user.token_version += 1
        user.save()

    @staticmethod
    def delete_user(user_id):
        try:
            User.objects.get(id=user_id).delete()
            return True
        except DoesNotExist:
            return False