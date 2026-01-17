from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from utils.roles import government_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['GET'])
@jwt_required()
@government_required
def get_users():
    users = User.query.all()
    users_list = [
        {
            'id': u.id,
            'full_name': u.full_name,
            'email': u.email,
            'role': u.role,
            'national_id': u.national_id
        } for u in users
    ]
    return jsonify(users_list)


# User detail and role change endpoint
@users_bp.route('/users/<int:user_id>', methods=['GET', 'PATCH'])
@jwt_required()
@government_required
def user_detail(user_id):
    from models.user import User
    from flask_jwt_extended import get_jwt_identity
    user = User.query.get_or_404(user_id)

    # Prevent self role change
    current_user_id = get_jwt_identity()

    if request.method == 'GET':
        data = {
            'id': user.id,
            'full_name': user.full_name,
            'gender': user.gender,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'age': user.age,
            'national_id': user.national_id,
            'role': user.role,
            'user_type': user.user_type,
            'work_place': user.work_place,
            'badge_number': user.badge_number,
            'journalist_id': user.journalist_id,
            'email': user.email
        }
        return jsonify(data)

    elif request.method == 'PATCH':
        data = request.get_json()
        # Only allow role change, not for self
        if 'role' in data:
            if user.id == current_user_id:
                abort(403, description="Cannot change your own role.")
            user.role = data['role']
            db.session.commit()
            return jsonify({'message': 'Role updated', 'role': user.role})
        abort(400, description="No valid fields to update.")


# User preferences update endpoint (for instant toggle saves)
@users_bp.route('/user/preferences', methods=['PATCH'])
@jwt_required()
def update_user_preferences():
    """Update user preferences like dark_mode instantly without full form submission"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    
    data = request.get_json()
    if not data:
        abort(400, description="No data provided")
    
    updated_fields = []
    
    # Only allow specific preference fields
    allowed_preferences = ['dark_mode', 'email_notifications', 'sms_alerts', 'system_alerts']
    
    for field in allowed_preferences:
        if field in data:
            setattr(user, field, bool(data[field]))
            updated_fields.append(field)
    
    if updated_fields:
        db.session.commit()
        return jsonify({
            'message': 'Preferences updated',
            'updated': updated_fields
        })
    
    abort(400, description="No valid preference fields to update.")
