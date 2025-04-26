from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from functools import wraps

from models import User
from main import db
from utils import decode_token

# Create blueprint
users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

# Decorator for token validation and role check
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        
        # Decode and validate token
        payload = decode_token(token)
        if not payload or payload.get('type') != 'access':
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Get user
        user_id = int(payload['sub'])
        current_user = User.query.filter_by(id=user_id).first()
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        if not current_user.is_active:
            return jsonify({"error": "User account is disabled"}), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({"error": "Admin privileges required"}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

def manager_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role not in ['admin', 'manager']:
            return jsonify({"error": "Manager privileges required"}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

@users_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user information"""
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }), 200

@users_bp.route('/me', methods=['PUT'])
@token_required
def update_current_user(current_user):
    """Update current user information"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    # Update fields
    if 'full_name' in data:
        current_user.full_name = data['full_name']
    
    if 'password' in data:
        current_user.set_password(data['password'])
    
    db.session.commit()
    
    return jsonify({
        "message": "User updated successfully",
        "user_id": current_user.id
    }), 200

@users_bp.route('', methods=['GET'])
@token_required
@manager_required
def get_users(current_user):
    """Get all users (manager/admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    users = User.query.paginate(page=page, per_page=per_page)
    
    result = []
    for user in users.items:
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        })
    
    return jsonify({
        "users": result,
        "total": users.total,
        "pages": users.pages,
        "current_page": users.page
    }), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@token_required
@manager_required
def get_user(current_user, user_id):
    """Get user by ID (manager/admin only)"""
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }), 200

@users_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_id):
    """Update user by ID (admin only)"""
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    # Update fields
    if 'email' in data:
        user.email = data['email']
    
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'role' in data:
        user.role = data['role']
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    if 'password' in data:
        user.set_password(data['password'])
    
    db.session.commit()
    
    return jsonify({
        "message": "User updated successfully",
        "user_id": user.id
    }), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    """Deactivate user by ID (admin only)"""
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Can't delete yourself
    if user.id == current_user.id:
        return jsonify({"error": "Cannot delete your own account"}), 403
    
    # Soft delete (deactivate)
    user.is_active = False
    db.session.commit()
    
    return jsonify({
        "message": "User deactivated successfully",
        "user_id": user.id
    }), 200