"""
Export Routes
=============
API endpoints for data export
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.accident import Accident
from models.user import User
from utils.export import (
    export_to_csv, export_to_excel, export_to_pdf,
    format_accident_for_export, format_user_for_export
)
from utils.audit import log_export

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


@export_bp.route('/accidents/<format_type>')
@jwt_required()
def export_accidents(format_type):
    """Export accidents in specified format"""
    
    # Get filters from query params
    governorate = request.args.get('governorate')
    severity = request.args.get('severity')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
    query = Accident.query
    
    if governorate:
        query = query.filter(Accident.governorate == governorate)
    if severity:
        query = query.filter(Accident.severity == severity)
    if start_date:
        from datetime import datetime
        try:
            query = query.filter(Accident.occurred_at >= datetime.fromisoformat(start_date))
        except:
            pass
    if end_date:
        from datetime import datetime
        try:
            query = query.filter(Accident.occurred_at <= datetime.fromisoformat(end_date))
        except:
            pass
    
    accidents = query.order_by(Accident.occurred_at.desc()).all()
    data = [format_accident_for_export(a) for a in accidents]
    
    # Log export
    log_export('accident', len(data), format_type)
    
    # Export based on format
    timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format_type == 'csv':
        return export_to_csv(data, f'accidents_{timestamp}.csv')
    elif format_type == 'excel':
        return export_to_excel(data, f'accidents_{timestamp}.xlsx', sheet_name='Accidents')
    elif format_type == 'pdf':
        return export_to_pdf(data, f'accidents_{timestamp}.pdf', title='Accident Report')
    else:
        return {'error': 'Invalid format. Use: csv, excel, pdf'}, 400


@export_bp.route('/users/<format_type>')
@jwt_required()
def export_users(format_type):
    """Export users in specified format (admin only)"""
    
    # Check admin permission
    from models.user import User as UserModel
    user_id = get_jwt_identity()
    user = UserModel.query.get(int(user_id))
    
    if not user or user.role not in ['admin', 'government']:
        return {'error': 'Unauthorized'}, 403
    
    users = User.query.all()
    data = [format_user_for_export(u) for u in users]
    
    # Log export
    log_export('user', len(data), format_type)
    
    # Export based on format
    timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format_type == 'csv':
        return export_to_csv(data, f'users_{timestamp}.csv')
    elif format_type == 'excel':
        return export_to_excel(data, f'users_{timestamp}.xlsx', sheet_name='Users')
    elif format_type == 'pdf':
        return export_to_pdf(data, f'users_{timestamp}.pdf', title='User Report')
    else:
        return {'error': 'Invalid format. Use: csv, excel, pdf'}, 400


@export_bp.route('/statistics/<format_type>')
@jwt_required()
def export_statistics(format_type):
    """Export statistics summary"""
    from sqlalchemy import func
    from extensions import db
    
    # Get aggregated stats
    stats = []
    
    # By governorate
    gov_stats = db.session.query(
        Accident.governorate,
        func.count(Accident.id).label('count')
    ).group_by(Accident.governorate).all()
    
    for gov, count in gov_stats:
        stats.append({
            'Category': 'By Governorate',
            'Item': gov or 'Unknown',
            'Count': count
        })
    
    # By severity
    sev_stats = db.session.query(
        Accident.severity,
        func.count(Accident.id).label('count')
    ).group_by(Accident.severity).all()
    
    for sev, count in sev_stats:
        stats.append({
            'Category': 'By Severity',
            'Item': sev or 'Unknown',
            'Count': count
        })
    
    # By cause
    cause_stats = db.session.query(
        Accident.cause,
        func.count(Accident.id).label('count')
    ).group_by(Accident.cause).all()
    
    for cause, count in cause_stats:
        stats.append({
            'Category': 'By Cause',
            'Item': cause or 'Unknown',
            'Count': count
        })
    
    # Log export
    log_export('statistics', len(stats), format_type)
    
    timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format_type == 'csv':
        return export_to_csv(stats, f'statistics_{timestamp}.csv')
    elif format_type == 'excel':
        return export_to_excel(stats, f'statistics_{timestamp}.xlsx', sheet_name='Statistics')
    elif format_type == 'pdf':
        return export_to_pdf(stats, f'statistics_{timestamp}.pdf', title='Statistics Report')
    else:
        return {'error': 'Invalid format. Use: csv, excel, pdf'}, 400
