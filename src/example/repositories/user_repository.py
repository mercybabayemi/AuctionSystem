from abc import ABC


class UserRepository(ABC):

    @staticmethod
    def find_user_by_id(user_id):
        pass

    @staticmethod
    def save_user(user):
        pass

    @staticmethod
    def find_user_by_username(username):
        pass

    @staticmethod
    def count():
        pass

    @staticmethod
    def invalidate_token(user_id):
        pass

    @staticmethod
    def delete_user(user_id):
        pass