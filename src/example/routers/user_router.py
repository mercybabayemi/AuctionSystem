from flask import Blueprint, request, jsonify, render_template, current_app
from flask_jwt_extended import get_current_user, jwt_required, get_jwt_identity
from jwt import PyJWTError
from werkzeug.exceptions import HTTPException

from ..exceptions.auth_error import AuthError
from ..exceptions.entity_not_found_exception import EntityNotFoundException
from ..exceptions.is_not_admin_exception import IsNotAdmin
from ..exceptions.validation_error import ValidationError
from ..repositories.user_repository_impl import UserRepositoryImpl
from ..services.user_service_impl import UserServiceImpl
from ..utils.token_util import decode_token

user_router = Blueprint('user', __name__, url_prefix='/api')
user_service = UserServiceImpl()

@user_router.route('/')
def home():
    return render_template('index.html')

@user_router.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    try:
        token = user_service.login(data.get('username'), data.get('password'))
        if token:
            return jsonify({"token": token}), 200
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422
    except EntityNotFoundException as e:
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@user_router.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    user_data = request.get_json()
    if not user_data:
        return jsonify({"error": "Invalid JSON data"}), 400
    try:
        user_service.register_user(user_data)
        return jsonify({"message": "User registered successfully"}), 201
    except ValidationError as e:
        return jsonify({"error": e}), 422
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_router.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = user_service.get_user(user_id)
        return jsonify(user), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@user_router.route('/user/<user_id>/block', methods=['POST'])
def block_user(user_id):
    try:
        user = get_current_user()
        if not user.is_admin() or user.is_super_admin():
            raise IsNotAdmin("Permission denied: Only admin can block users.")
        user_service.block_user(user_id)
        return jsonify({"message": "User blocked successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_router.route('/create_admin', methods=['POST'])
@jwt_required()
def create_admin():
    try:
        # Get token from header manually (compatible with your system)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid header"}), 401

        token = auth_header.split()[1]
        current_user_id = decode_token(token)  # Using your existing decode

        # DEBUG: Print user ID and fetch full user
        current_app.logger.debug(f"Attempting admin creation as user: {current_user_id}")
        user = UserRepositoryImpl.find_user_by_id(current_user_id)

        # DEBUG: Print user object and super admin status
        current_app.logger.debug(f"User object: {user.to_dict() if user else None}")
        current_app.logger.debug(f"Super admin status: {getattr(user, 'is_super_admin', None)}")
        current_app.logger.debug(f"User data: {user.to_dict()}")
        if not user:
            return jsonify({"error": "User not found"}), 404

        # PROPER Super admin check - looks in roles sub-document
        is_super_admin = user.roles.get('is_super_admin', False) if hasattr(user, 'roles') else False

        if not is_super_admin:
            current_app.logger.warning(f"Admin creation denied for user {user.user_id}")
            return jsonify({"error": "Super admin privileges required"}), 403

        # Process request
        admin_data = request.get_json()
        UserServiceImpl.create_admin_account(admin_data)

        return jsonify({
            "message": "Admin created successfully"
        }), 201

    except AuthError as e:  # Your custom exception
        current_app.logger.error(f"Auth failed: {str(e)}")
        return jsonify({"error": str(e)}), 401
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Admin creation failed: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

 
@user_router.route('/auction_report', methods=['GET'])
@jwt_required()
def generate_auction_report():
    try:
        # Get token from header manually (compatible with your system)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid header"}), 401

        token = auth_header.split()[1]
        current_user_id = decode_token(token)  # Using your existing decode

        # DEBUG: Print user ID and fetch full user
        current_app.logger.debug(f"Attempting admin creation as user: {current_user_id}")
        user = UserRepositoryImpl.find_user_by_id(current_user_id)

        # DEBUG: Print user object and super admin status
        current_app.logger.debug(f"User object: {user.to_dict() if user else None}")
        current_app.logger.debug(f"Super admin status: {getattr(user, 'is_super_admin', None)}")
        current_app.logger.debug(f"User data: {user.to_dict()}")
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Check permissions - EITHER superadmin OR admin
        roles = getattr(user, 'roles', {})
        is_authorized = roles.get('is_super_admin', False) or roles.get('is_admin', False)

        if not is_authorized:
            current_app.logger.warning(f"Report access denied for user {user.user_id}")
            return jsonify({"error": "Admin privileges required"}), 403

        # Generate report
        report = user_service.generate_report()
        return jsonify(report), 200
    except AuthError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        current_app.logger.exception("Report generation failed")
        return jsonify({"error": str(e)}), 500

@user_router.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        # Get token from header manually (compatible with your system)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid header"}), 401

        token = auth_header.split()[1]
        current_user_id = decode_token(token)  # Using your existing decode

        # DEBUG: Print user ID and fetch full user
        current_app.logger.debug(f"Attempting admin creation as user: {current_user_id}")
        user = UserRepositoryImpl.find_user_by_id(current_user_id)

        # DEBUG: Print user object and super admin status
        current_app.logger.debug(f"User object: {user.to_dict() if user else None}")
        current_app.logger.debug(f"Super admin status: {getattr(user, 'is_super_admin', None)}")
        current_app.logger.debug(f"User data: {user.to_dict()}")
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(UserServiceImpl.logout(user.user_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_router.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        # Get token from header manually (compatible with your system)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid header"}), 401

        token = auth_header.split()[1]
        current_user_id = decode_token(token)  # Using your existing decode

        # DEBUG: Print user ID and fetch full user
        current_app.logger.debug(f"Attempting admin creation as user: {current_user_id}")
        user = UserRepositoryImpl.find_user_by_id(current_user_id)

        # DEBUG: Print user object and super admin status
        current_app.logger.debug(f"User object: {user.to_dict() if user else None}")
        current_app.logger.debug(f"Super admin status: {getattr(user, 'is_super_admin', None)}")
        current_app.logger.debug(f"User data: {user.to_dict()}")
        if not user:
            return jsonify({"error": "User not found"}), 404

        # PROPER Super admin check - looks in roles sub-document
        is_super_admin = user.roles.get('is_super_admin', False) if hasattr(user, 'roles') else False

        if not is_super_admin:
            current_app.logger.warning(f"Admin creation denied for user {user.user_id}")
            return jsonify({"error": "Super admin privileges required"}), 403

        UserServiceImpl.delete_user(user_id)
        return jsonify("Account deleted successfully"), 200

    except AuthError as e:  # Your custom exception
        current_app.logger.error(f"Auth failed: {str(e)}")
        return jsonify({"error": str(e)}), 401
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500