import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fixed-256-bit-secret-key-123456'
    JWT_EXPIRATION_SECONDS = 3600  # 1 hour
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../static/uploads/auction_images')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}