import os
import pyotp
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from models import User, RefreshToken
from main import db
from utils import create_access_token, create_refresh_token, verify_password, decode_token

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# In-memory storage for TOTP secrets (in production, this should be stored in Redis or similar)
totp_secrets = {}

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
        
    # Validate required fields
    required_fields = ['email', 'password', 'full_name']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 400
    
    # Create new user
    new_user = User(
        email=data['email'],
        full_name=data['full_name'],
        role=data.get('role', 'user')
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        "message": "User created successfully",
        "user_id": new_user.id
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate and log in a user"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
        
    # Validate required fields
    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    if not user.is_active:
        return jsonify({"error": "User account is disabled"}), 401
    
    # Generate TOTP code and send it (simulated here)
    totp_code, secret = generate_totp_code(user.email)
    
    # In a real app, you would send this code via email or SMS
    # For demonstration, we're just returning it
    return jsonify({
        "message": "Authentication code sent to your email",
        "temp_token": secret,  # This would not be returned in a real app
        "code": totp_code  # This would not be returned in a real app
    }), 200

@auth_bp.route('/verify', methods=['POST'])
def verify_totp():
    """Verify TOTP code and issue tokens"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
        
    # Validate required fields
    required_fields = ['email', 'code']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Verify TOTP code
    is_valid = verify_totp(data['email'], data['code'])
    if not is_valid:
        return jsonify({"error": "Invalid or expired code"}), 401
    
    # Get user
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Store refresh token in database
    db_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        is_valid=True,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(db_token)
    db.session.commit()
    
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    data = request.get_json()
    
    if not data or 'refresh_token' not in data:
        return jsonify({"error": "Refresh token is required"}), 400
    
    refresh_token = data['refresh_token']
    
    # Decode token
    payload = decode_token(refresh_token)
    if not payload or payload.get('type') != 'refresh':
        return jsonify({"error": "Invalid refresh token"}), 401
    
    # Check if token exists in database and is valid
    db_token = RefreshToken.query.filter_by(
        token=refresh_token,
        is_valid=True,
        user_id=int(payload['sub'])
    ).first()
    
    if not db_token or db_token.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired refresh token"}), 401
    
    # Generate new tokens
    user_id = int(payload['sub'])
    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    
    # Invalidate old token and create new one
    db_token.is_valid = False
    db.session.add(db_token)
    
    new_db_token = RefreshToken(
        token=new_refresh_token,
        user_id=user_id,
        is_valid=True,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(new_db_token)
    db.session.commit()
    
    return jsonify({
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Invalidate the refresh token (logout)"""
    auth_header = request.headers.get('Authorization')
    data = request.get_json()
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401
    
    access_token = auth_header.split(' ')[1]
    
    # Decode token
    payload = decode_token(access_token)
    if not payload or payload.get('type') != 'access':
        return jsonify({"error": "Invalid access token"}), 401
    
    user_id = int(payload['sub'])
    
    # Get refresh token from request
    if not data or 'refresh_token' not in data:
        return jsonify({"error": "Refresh token is required"}), 400
    
    refresh_token = data['refresh_token']
    
    # Invalidate refresh token
    token = RefreshToken.query.filter_by(
        token=refresh_token,
        user_id=user_id,
        is_valid=True
    ).first()
    
    if token:
        token.is_valid = False
        db.session.commit()
    
    return jsonify({"message": "Logged out successfully"}), 200

# Helper functions for TOTP
def generate_totp_code(email):
    """Generate a TOTP code for a user"""
    secret = pyotp.random_base32()
    totp_secrets[email] = {
        "secret": secret,
        "created_at": datetime.utcnow()
    }
    totp = pyotp.TOTP(secret, digits=6, interval=30)
    return totp.now(), secret

def verify_totp(email, code):
    """Verify a TOTP code for a user"""
    if email not in totp_secrets:
        return False
    
    # Check if TOTP secret is expired (5 minutes)
    created_at = totp_secrets[email]["created_at"]
    if datetime.utcnow() - created_at > timedelta(minutes=5):
        del totp_secrets[email]
        return False
    
    secret = totp_secrets[email]["secret"]
    totp = pyotp.TOTP(secret, digits=6, interval=30)
    return totp.verify(code)