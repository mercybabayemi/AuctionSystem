from functools import wraps
from flask import request, jsonify, current_app
from src.example.utils.token_util import decode_token
from src.example.exceptions.auth_error import AuthError # Your custom AuthError

def manual_jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401
        
        parts = auth_header.split()

        if parts[0].lower() != 'bearer' or len(parts) == 1 or len(parts) > 2:
            return jsonify({"error": "Invalid token header. Expected 'Bearer <token>'"}), 401
        
        token = parts[1]
        
        try:
            user_id = decode_token(token) # decode_token should handle internal validation
            # Pass the user_id to the decorated function
            # The decorated function can then fetch the full user object if needed
            return fn(current_user_id=user_id, *args, **kwargs)
        except AuthError as e: # Catching the specific AuthError from decode_token
            current_app.logger.warning(f"Authentication failed: {str(e)}") # Log as warning or info
            return jsonify({"error": str(e)}), 401 # Return the message from AuthError
        except Exception as e: # Catch any other unexpected errors during token processing
            current_app.logger.error(f"Unexpected error during token authentication: {str(e)}")
            return jsonify({"error": "An unexpected error occurred during authentication"}), 500
    return wrapper
