"""
File Upload Routes
==================
API endpoints for file uploads
"""

from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.file_upload import save_file, delete_file, get_file_url, get_files_for_entity, get_upload_folder

upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')


@upload_bp.route('', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    entity_type = request.form.get('entity_type')
    entity_id = request.form.get('entity_id')
    allowed_types = request.form.get('allowed_types', 'all')
    
    user_id = get_jwt_identity()
    
    uploaded_file, error = save_file(
        file,
        entity_type=entity_type,
        entity_id=int(entity_id) if entity_id else None,
        user_id=int(user_id) if user_id else None,
        allowed_types=allowed_types
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'file': uploaded_file.to_dict(),
        'url': get_file_url(uploaded_file)
    }), 201


@upload_bp.route('/image', methods=['POST'])
@jwt_required()
def upload_image():
    """Upload an image file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    entity_type = request.form.get('entity_type')
    entity_id = request.form.get('entity_id')
    
    user_id = get_jwt_identity()
    
    uploaded_file, error = save_file(
        file,
        entity_type=entity_type,
        entity_id=int(entity_id) if entity_id else None,
        user_id=int(user_id) if user_id else None,
        allowed_types='image'
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'file': uploaded_file.to_dict(),
        'url': get_file_url(uploaded_file)
    }), 201


@upload_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_uploaded_file(file_id):
    """Delete an uploaded file"""
    from models.uploaded_file import UploadedFile
    
    uploaded_file = UploadedFile.query.get(file_id)
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    # Check permission
    user_id = get_jwt_identity()
    if uploaded_file.uploaded_by != int(user_id):
        # Allow admin to delete any file
        from models.user import User
        user = User.query.get(int(user_id))
        if not user or user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
    
    success, error = delete_file(file_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'success': True}), 200


@upload_bp.route('/entity/<entity_type>/<int:entity_id>', methods=['GET'])
@jwt_required()
def get_entity_files(entity_type, entity_id):
    """Get all files for an entity"""
    files = get_files_for_entity(entity_type, entity_id)
    
    return jsonify({
        'files': [
            {
                **f.to_dict(),
                'url': get_file_url(f)
            }
            for f in files
        ]
    })


@upload_bp.route('/serve/<filename>')
def serve_file(filename):
    """Serve an uploaded file"""
    return send_from_directory(get_upload_folder(), filename)
