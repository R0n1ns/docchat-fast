import os
from flask import Flask, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up database base class
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create and configure the app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secure-document-management-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Fix for proxy headers
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize extensions
db.init_app(app)

# Import blueprints
from api.v1.auth import auth_bp
from api.v1.users import users_bp
from api.v1.documents import documents_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(documents_bp)

# Basic routes
@app.route('/')
def index():
    return redirect(url_for('api_docs'))

@app.route('/api/docs')
def api_docs():
    return jsonify({
        "message": "Secure Document Management API",
        "version": "1.0.0",
        "description": "API for secure document management with encryption and integrity verification",
        "endpoints": {
            "Authentication": {
                "base_url": "/api/v1/auth",
                "endpoints": [
                    {"path": "/register", "method": "POST", "description": "Register a new user"},
                    {"path": "/login", "method": "POST", "description": "Authenticate and get TOTP code"},
                    {"path": "/verify", "method": "POST", "description": "Verify TOTP code and get tokens"},
                    {"path": "/refresh", "method": "POST", "description": "Refresh access token"},
                    {"path": "/logout", "method": "POST", "description": "Invalidate refresh token (logout)"}
                ]
            },
            "Users": {
                "base_url": "/api/v1/users",
                "endpoints": [
                    {"path": "/me", "method": "GET", "description": "Get current user information"},
                    {"path": "/me", "method": "PUT", "description": "Update current user information"},
                    {"path": "", "method": "GET", "description": "Get all users (manager/admin only)"},
                    {"path": "/{user_id}", "method": "GET", "description": "Get user by ID (manager/admin only)"},
                    {"path": "/{user_id}", "method": "PUT", "description": "Update user by ID (admin only)"},
                    {"path": "/{user_id}", "method": "DELETE", "description": "Deactivate user by ID (admin only)"}
                ]
            },
            "Documents": {
                "base_url": "/api/v1/documents",
                "endpoints": [
                    {"path": "", "method": "POST", "description": "Create a new document"},
                    {"path": "", "method": "GET", "description": "List documents with pagination and filtering"},
                    {"path": "/{document_id}", "method": "GET", "description": "Get document by ID with all versions"},
                    {"path": "/{document_id}/download", "method": "GET", "description": "Download the current version of a document"},
                    {"path": "/{document_id}/versions/{version_id}", "method": "GET", "description": "Download a specific version of a document"},
                    {"path": "/{document_id}", "method": "PUT", "description": "Update document metadata or add a new version"},
                    {"path": "/{document_id}", "method": "DELETE", "description": "Mark document as deleted (soft delete)"},
                    {"path": "/{document_id}/verify", "method": "GET", "description": "Verify the integrity of a document"}
                ]
            }
        }
    })

# Create tables
with app.app_context():
    from models import User, Document, DocumentVersion, RefreshToken
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
