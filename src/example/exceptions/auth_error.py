class AuthError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.code = 401