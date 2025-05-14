from flask import Flask, render_template, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from mongoengine import connect
from config import Config
from example.services.auction_service_impl import AuctionServiceImpl
from src.example.routers.user_router import user_router
from src.example.routers.auction_router import auction_router
# AuctionServiceImpl is imported by auction_router, no need to import here if not directly used
# from src.example.services.auction_service_impl import AuctionServiceImpl

# Import socketio instance from extensions and initialize it with the app
from .extensions import socketio

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Initialize extensions
socketio.init_app(app)
connect('auction_db')
JWTManager(app)

app.register_blueprint(user_router, url_prefix='/api')
app.register_blueprint(auction_router, url_prefix='/api')


# --- Frontend Routes ---

@app.route('/')
def index():
    try:
        # Fetch auctions using the service layer
        # Assuming list_items() returns a list of Auction model objects
        raw_auctions = AuctionServiceImpl.list_items() 
        
        # Process auctions for template rendering
        processed_auctions = []
        for auction in raw_auctions:
            # TODO: Fetch actual highest bid from Bid collection for this auction.id
            # TODO: Calculate actual time_left based on auction.end_time
            current_bid_placeholder = auction.starting_bid # Use starting bid as placeholder
            time_left_placeholder = "Time Left Placeholder" # Placeholder

            processed_auctions.append({
                'id': str(auction.id), # Important: Pass ID as string
                'title': auction.item_name, 
                'image_url': url_for('static', filename='images/placeholder.png'), # Static placeholder image
                'current_bid': f"${current_bid_placeholder:.2f}", # Format placeholder bid
                'time_left': time_left_placeholder
            })
            
    except Exception as e:
        print(f"Error fetching auctions for index route: {e}")
        processed_auctions = [] # Render empty list or show error message on template
        
    return render_template('index.html', auctions=processed_auctions)


if __name__ == '__main__':
    # Use socketio.run from extensions
    print("Starting Flask-SocketIO server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)