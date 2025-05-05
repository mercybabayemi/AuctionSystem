from flask import Flask
from flask_jwt_extended import JWTManager
from mongoengine import connect
from config import Config

from src.example.routers.user_router import user_router
from src.example.routers.auction_router import auction_router

app = Flask(__name__)
app.config.from_object(Config)
connect('auction_db')
JWTManager(app)

app.register_blueprint(user_router, url_prefix='/api')
app.register_blueprint(auction_router, url_prefix='/api')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)