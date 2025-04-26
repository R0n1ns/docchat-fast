import os
import uuid
import hashlib
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from functools import wraps
from werkzeug.utils import secure_filename

from models import User, Document, DocumentVersion
from main import db
from utils import decode_token, encrypt_file, decrypt_file
from api.v1.users import token_required

# Create blueprint
documents_bp = Blueprint('documents', __name__, url_prefix='/api/v1/documents')

# Mock storage path (would use MinIO or S3 in production)
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@documents_bp.route('', methods=['POST'])
@token_required
def create_document(current_user):
    """Create a new document"""
    # Check if file is included
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Get form data
    title = request.form.get('title')
    description = request.form.get('description', '')
    
    if not title:
        return jsonify({"error": "Title is required"}), 400
    
    # Process file
    filename = secure_filename(file.filename)
    content_type = file.content_type or 'application/octet-stream'
    file_content = file.read()
    file_size = len(file_content)
    
    # Generate unique storage path
    storage_path = f"{UPLOAD_FOLDER}/{current_user.id}_{uuid.uuid4()}"
    
    # Encrypt file content and save
    encrypted_content, nonce = encrypt_file(file_content)
    with open(storage_path, 'wb') as f:
        f.write(encrypted_content)
    
    # Calculate SHA-256 hash of original content
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Create document
    document = Document(
        title=title,
        description=description,
        filename=filename,
        content_type=content_type,
        creator_id=current_user.id
    )
    db.session.add(document)
    db.session.flush()
    
    # Create first version
    version = DocumentVersion(
        document_id=document.id,
        user_id=current_user.id,
        version_number=1,
        filename=filename,
        content_type=content_type,
        file_size=file_size,
        storage_path=storage_path,
        nonce=nonce.hex(),
        file_hash=file_hash,
        prev_hash=None,  # First version, no previous hash
        file_metadata={"original_name": filename}
    )
    db.session.add(version)
    db.session.flush()
    
    # Update document with current version id
    document.current_version_id = version.id
    db.session.commit()
    
    return jsonify({
        "message": "Document created successfully",
        "document_id": document.id,
        "version_id": version.id
    }), 201

@documents_bp.route('', methods=['GET'])
@token_required
def list_documents(current_user):
    """List documents with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    title = request.args.get('title', '')
    creator_id = request.args.get('creator_id', type=int)
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Build query
    query = Document.query.filter_by(is_deleted=False)
    
    # Apply filters
    if title:
        query = query.filter(Document.title.ilike(f'%{title}%'))
    
    if creator_id:
        query = query.filter_by(creator_id=creator_id)
    
    # Apply sorting
    if sort_order.lower() == 'asc':
        query = query.order_by(getattr(Document, sort_by).asc())
    else:
        query = query.order_by(getattr(Document, sort_by).desc())
    
    # Paginate
    documents = query.paginate(page=page, per_page=per_page)
    
    result = []
    for doc in documents.items:
        result.append({
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "creator_id": doc.creator_id,
            "current_version_id": doc.current_version_id,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        })
    
    return jsonify({
        "documents": result,
        "total": documents.total,
        "pages": documents.pages,
        "current_page": documents.page
    }), 200

@documents_bp.route('/<int:document_id>', methods=['GET'])
@token_required
def get_document(current_user, document_id):
    """Get document by ID with all versions"""
    document = Document.query.filter_by(id=document_id, is_deleted=False).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    # Get all versions
    versions = DocumentVersion.query.filter_by(document_id=document_id).order_by(DocumentVersion.version_number.desc()).all()
    
    versions_list = []
    for v in versions:
        versions_list.append({
            "id": v.id,
            "version_number": v.version_number,
            "filename": v.filename,
            "content_type": v.content_type,
            "file_size": v.file_size,
            "file_hash": v.file_hash,
            "prev_hash": v.prev_hash,
            "created_at": v.created_at,
            "user_id": v.user_id
        })
    
    return jsonify({
        "document": {
            "id": document.id,
            "title": document.title,
            "description": document.description,
            "filename": document.filename,
            "content_type": document.content_type,
            "creator_id": document.creator_id,
            "current_version_id": document.current_version_id,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        },
        "versions": versions_list
    }), 200

@documents_bp.route('/<int:document_id>/download', methods=['GET'])
@token_required
def download_document(current_user, document_id):
    """Download the current version of a document"""
    document = Document.query.filter_by(id=document_id, is_deleted=False).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    if not document.current_version_id:
        return jsonify({"error": "Document has no versions"}), 404
    
    # Get current version
    version = DocumentVersion.query.filter_by(id=document.current_version_id).first()
    
    if not version:
        return jsonify({"error": "Document version not found"}), 404
    
    # Read and decrypt file
    try:
        with open(version.storage_path, 'rb') as f:
            encrypted_content = f.read()
        
        nonce = bytes.fromhex(version.nonce)
        decrypted_content = decrypt_file(encrypted_content, nonce)
        
        return send_file(
            io.BytesIO(decrypted_content),
            mimetype=version.content_type,
            as_attachment=True,
            download_name=version.filename
        )
    except Exception as e:
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 500

@documents_bp.route('/<int:document_id>/versions/<int:version_id>', methods=['GET'])
@token_required
def download_document_version(current_user, document_id, version_id):
    """Download a specific version of a document"""
    document = Document.query.filter_by(id=document_id, is_deleted=False).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    # Get specific version
    version = DocumentVersion.query.filter_by(id=version_id, document_id=document_id).first()
    
    if not version:
        return jsonify({"error": "Document version not found"}), 404
    
    # Read and decrypt file
    try:
        with open(version.storage_path, 'rb') as f:
            encrypted_content = f.read()
        
        nonce = bytes.fromhex(version.nonce)
        decrypted_content = decrypt_file(encrypted_content, nonce)
        
        return send_file(
            io.BytesIO(decrypted_content),
            mimetype=version.content_type,
            as_attachment=True,
            download_name=version.filename
        )
    except Exception as e:
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 500

@documents_bp.route('/<int:document_id>', methods=['PUT'])
@token_required
def update_document(current_user, document_id):
    """Update document metadata or add a new version"""
    document = Document.query.filter_by(id=document_id, is_deleted=False).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    # Get form/JSON data
    if request.is_json:
        data = request.get_json()
        
        # Update document metadata
        if 'title' in data:
            document.title = data['title']
        
        if 'description' in data:
            document.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            "message": "Document updated successfully",
            "document_id": document.id
        }), 200
    else:
        # Check if file is included for new version
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded for new version"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Update document metadata if provided
        if title:
            document.title = title
        
        if description:
            document.description = description
        
        # Process file
        filename = secure_filename(file.filename)
        content_type = file.content_type or 'application/octet-stream'
        file_content = file.read()
        file_size = len(file_content)
        
        # Generate unique storage path
        storage_path = f"{UPLOAD_FOLDER}/{current_user.id}_{uuid.uuid4()}"
        
        # Encrypt file content and save
        encrypted_content, nonce = encrypt_file(file_content)
        with open(storage_path, 'wb') as f:
            f.write(encrypted_content)
        
        # Calculate SHA-256 hash of original content
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Get current version for prev_hash
        current_version = DocumentVersion.query.filter_by(id=document.current_version_id).first()
        prev_hash = current_version.file_hash if current_version else None
        
        # Get latest version number
        last_version = DocumentVersion.query.filter_by(document_id=document_id).order_by(DocumentVersion.version_number.desc()).first()
        version_number = (last_version.version_number + 1) if last_version else 1
        
        # Create new version
        version = DocumentVersion(
            document_id=document.id,
            user_id=current_user.id,
            version_number=version_number,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            storage_path=storage_path,
            nonce=nonce.hex(),
            file_hash=file_hash,
            prev_hash=prev_hash,
            file_metadata={"original_name": filename}
        )
        db.session.add(version)
        db.session.flush()
        
        # Update document with current version id and metadata
        document.current_version_id = version.id
        document.filename = filename
        document.content_type = content_type
        db.session.commit()
        
        return jsonify({
            "message": "Document updated with new version",
            "document_id": document.id,
            "version_id": version.id,
            "version_number": version.version_number
        }), 200

@documents_bp.route('/<int:document_id>', methods=['DELETE'])
@token_required
def delete_document(current_user, document_id):
    """Mark document as deleted (soft delete)"""
    document = Document.query.filter_by(id=document_id, is_deleted=False).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    # Soft delete
    document.is_deleted = True
    db.session.commit()
    
    return jsonify({
        "message": "Document deleted successfully",
        "document_id": document.id
    }), 200

@documents_bp.route('/<int:document_id>/verify', methods=['GET'])
@token_required
def verify_document_integrity(current_user, document_id):
    """Verify the integrity of a document by checking the hash chain"""
    document = Document.query.filter_by(id=document_id).first()
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    # Get all versions in chronological order
    versions = DocumentVersion.query.filter_by(document_id=document_id).order_by(DocumentVersion.version_number.asc()).all()
    
    if not versions:
        return jsonify({"error": "Document has no versions"}), 404
    
    # Check first version has no prev_hash
    if versions[0].prev_hash is not None:
        return jsonify({
            "verified": False,
            "error": "First version has a previous hash set, which is invalid"
        }), 200
    
    # Check all subsequent versions
    for i in range(1, len(versions)):
        if versions[i].prev_hash != versions[i-1].file_hash:
            return jsonify({
                "verified": False,
                "error": f"Hash chain broken at version {versions[i].version_number}"
            }), 200
    
    return jsonify({
        "verified": True,
        "message": "Document integrity verified",
        "versions_count": len(versions)
    }), 200