from werkzeug.security import check_password_hash, generate_password_hash

from src.example.models.auction import Auction
from src.example.repositories.user_repository_impl import UserRepositoryImpl
from src.example.schemas.user_schema import UserSchema
from src.example.services.user_service import UserService
from src.example.utils.token_util import generate_token


class UserServiceImpl(UserService):
    @staticmethod
    def register_user(user_data):
        user_schema = UserSchema()
        user = user_schema.load(user_data)
        user.password = generate_password_hash(user.password)
        UserRepositoryImpl.save_user(user)

    @staticmethod
    def get_user(user_id):
        user = UserRepositoryImpl.find_user_by_id(user_id)
        if user:
            return UserSchema().dump(user)  # Proper serialization
        return None

    @staticmethod
    def login(username, password):
        user = UserRepositoryImpl.find_user_by_username(username)
        if user and check_password_hash(user.password, password):
            try:
                return generate_token(user)
            except Exception as e:
                return f"Token generation failed: {str(e)}"
        return None

    @staticmethod
    def block_user(user_id):
        user = UserRepositoryImpl.find_user_by_id(user_id)
        user.is_blocked = True
        user.save()

    @staticmethod
    def create_admin_account(user_data):
        user_schema = UserSchema()
        user = user_schema.load(user_data)
        user.roles['is_admin'] = True
        UserRepositoryImpl.save_user(user)

    @staticmethod
    def generate_report():
        auctions = Auction.objects.all()
        return [auctions.to_dict() for auction in auctions]

    @staticmethod
    def logout(user_id):
        UserRepositoryImpl.invalidate_token(user_id)
        return {"message": "Logged out successfully"}

    @staticmethod
    def delete_user(target_user_id):
        try:
            UserRepositoryImpl.delete_user(target_user_id)
            return {"message": "User deleted successfully"}
        except ValueError as e:
            return f"Value error: {str(e)}"
        except Exception as e:
            return f"Exception: {str(e)}"
