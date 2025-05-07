from flask_socketio import SocketIO, join_room, leave_room

# Initialize SocketIO globally but without app instance yet
socketio = SocketIO(cors_allowed_origins="*") # Allow all origins for development

# --- SocketIO Event Handlers ---

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_auction')
def handle_join_auction_room(data):
    auction_id = data.get('auction_id')
    if auction_id:
        join_room(auction_id)
        print(f"Client joined room: {auction_id}")
        # Optionally send confirmation or current state back to client

@socketio.on('leave_auction')
def handle_leave_auction_room(data):
    auction_id = data.get('auction_id')
    if auction_id:
        leave_room(auction_id)
        print(f"Client left room: {auction_id}")

# Example function to call when a new bid is saved in your backend logic
def broadcast_new_bid(auction_id, bid_data):
    print(f"Broadcasting new bid for auction {auction_id}: {bid_data}")
    # Emit to a specific room associated with the auction
    socketio.emit('update_bid', bid_data, room=auction_id)

# --- End SocketIO Event Handlers ---
