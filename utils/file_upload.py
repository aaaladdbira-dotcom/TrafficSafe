"""
File Upload Service
===================
Handle file uploads securely
"""

import os
import uuid
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from extensions import db
from models.uploaded_file import UploadedFile


# Allowed file types
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'txt'},
    'all': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 'txt'}
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def get_upload_folder():
    """Get the upload folder path"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_folder = os.path.join(base_dir, 'static', 'uploads')
    
    # Create if doesn't exist
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    return upload_folder


def allowed_file(filename, file_type='all'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(file_type, ALLOWED_EXTENSIONS['all'])


def get_file_type(filename):
    """Determine file type from extension"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext in ALLOWED_EXTENSIONS['image']:
        return 'image'
    elif ext in ALLOWED_EXTENSIONS['document']:
        return 'document'
    return 'other'


def save_file(file, entity_type=None, entity_id=None, user_id=None, allowed_types='all'):
    """
    Save an uploaded file.
    
    Args:
        file: FileStorage object from request.files
        entity_type: Type of entity this file belongs to (e.g., 'accident_report')
        entity_id: ID of the entity
        user_id: ID of the uploading user
        allowed_types: 'image', 'document', or 'all'
    
    Returns:
        UploadedFile object or None
    """
    if not file or not file.filename:
        return None, "No file provided"
    
    # Check filename
    original_filename = secure_filename(file.filename)
    if not original_filename:
        return None, "Invalid filename"
    
    # Check extension
    if not allowed_file(original_filename, allowed_types):
        return None, f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS[allowed_types])}"
    
    # Check size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        return None, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Generate unique filename
    ext = original_filename.rsplit('.', 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    
    # Get MIME type
    mime_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
    
    # Save file
    upload_folder = get_upload_folder()
    file_path = os.path.join(upload_folder, stored_filename)
    
    try:
        file.save(file_path)
    except Exception as e:
        return None, f"Error saving file: {str(e)}"
    
    # Create database record
    uploaded_file = UploadedFile(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=get_file_type(original_filename),
        mime_type=mime_type,
        file_size=size,
        entity_type=entity_type,
        entity_id=entity_id,
        uploaded_by=user_id
    )
    
    db.session.add(uploaded_file)
    db.session.commit()
    
    return uploaded_file, None


def delete_file(file_id):
    """Delete an uploaded file"""
    uploaded_file = UploadedFile.query.get(file_id)
    if not uploaded_file:
        return False, "File not found"
    
    # Delete physical file
    upload_folder = get_upload_folder()
    file_path = os.path.join(upload_folder, uploaded_file.stored_filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete database record
    db.session.delete(uploaded_file)
    db.session.commit()
    
    return True, None


def get_file_url(uploaded_file):
    """Get the URL for an uploaded file"""
    return f"/static/uploads/{uploaded_file.stored_filename}"


def get_files_for_entity(entity_type, entity_id):
    """Get all files associated with an entity"""
    return UploadedFile.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).all()
