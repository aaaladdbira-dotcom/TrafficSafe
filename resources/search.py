"""
Search Routes
=============
Global search API endpoint
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from models.accident import Accident
from models.user import User

search_bp = Blueprint('search', __name__, url_prefix='/api')


@search_bp.route('/search', methods=['GET'])
@jwt_required()
def global_search():
    """
    Global search endpoint
    Searches accidents, users, and more
    
    Query params:
    - q: search query (required)
    - limit: max results per category (default 10)
    """
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)
    
    if not query or len(query) < 2:
        return jsonify({
            'accidents': [],
            'users': [],
            'query': query
        })
    
    results = {
        'accidents': [],
        'users': [],
        'query': query
    }
    
    # Search accidents
    search_term = f"%{query}%"
    accidents = Accident.query.filter(
        or_(
            Accident.governorate.ilike(search_term),
            Accident.delegation.ilike(search_term),
            Accident.cause.ilike(search_term),
            Accident.vehicle_type.ilike(search_term),
            Accident.description.ilike(search_term),
            Accident.severity.ilike(search_term)
        )
    ).order_by(Accident.occurred_at.desc()).limit(limit).all()
    
    results['accidents'] = [
        {
            'id': a.id,
            'governorate': a.governorate,
            'delegation': a.delegation,
            'severity': a.severity,
            'cause': a.cause,
            'occurred_at': a.occurred_at.isoformat() if a.occurred_at else None,
            'location': f"{a.governorate}, {a.delegation}" if a.delegation else a.governorate
        }
        for a in accidents
    ]
    
    # Search users (if admin/government)
    user_id = get_jwt_identity()
    current_user = User.query.get(int(user_id))
    
    if current_user and current_user.role in ['admin', 'government']:
        users = User.query.filter(
            or_(
                User.email.ilike(search_term),
                User.full_name.ilike(search_term),
                User.role.ilike(search_term)
            )
        ).limit(limit).all()
        
        results['users'] = [
            {
                'id': u.id,
                'email': u.email,
                'full_name': u.full_name,
                'role': u.role
            }
            for u in users
        ]
    
    return jsonify(results)
