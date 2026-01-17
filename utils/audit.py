"""
Audit Service
=============
Utility functions to log audit events
"""

import json
from flask import request, g
from extensions import db
from models.audit_log import AuditLog


def log_action(action, entity_type, entity_id=None, old_values=None, new_values=None, description=None, user_id=None, user_email=None):
    """
    Log an audit action.
    
    Args:
        action: The action performed (create, update, delete, login, export, etc.)
        entity_type: The type of entity (accident, user, report, etc.)
        entity_id: The ID of the entity affected
        old_values: Dict of old values (for updates)
        new_values: Dict of new values (for creates/updates)
        description: Human-readable description
        user_id: Override user ID (defaults to current user)
        user_email: Override user email
    """
    try:
        # Get current user from context
        if user_id is None:
            user_id = getattr(g, 'user_id', None)
        if user_email is None:
            user_email = getattr(g, 'user_email', None)
        
        # Get request context
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string[:500] if request.user_agent else None
        
        # Create log entry
        log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log
        
    except Exception as e:
        # Don't fail if audit logging fails
        print(f"Audit log error: {e}")
        db.session.rollback()
        return None


def log_login(user, success=True):
    """Log a login attempt"""
    return log_action(
        action='login_success' if success else 'login_failed',
        entity_type='user',
        entity_id=user.id if hasattr(user, 'id') else None,
        description=f"{'Successful' if success else 'Failed'} login for {user.email if hasattr(user, 'email') else user}",
        user_id=user.id if hasattr(user, 'id') else None,
        user_email=user.email if hasattr(user, 'email') else str(user)
    )


def log_create(entity_type, entity, description=None):
    """Log entity creation"""
    return log_action(
        action='create',
        entity_type=entity_type,
        entity_id=entity.id if hasattr(entity, 'id') else None,
        new_values=entity.to_dict() if hasattr(entity, 'to_dict') else None,
        description=description or f"Created {entity_type}"
    )


def log_update(entity_type, entity, old_values, description=None):
    """Log entity update"""
    new_values = entity.to_dict() if hasattr(entity, 'to_dict') else None
    return log_action(
        action='update',
        entity_type=entity_type,
        entity_id=entity.id if hasattr(entity, 'id') else None,
        old_values=old_values,
        new_values=new_values,
        description=description or f"Updated {entity_type}"
    )


def log_delete(entity_type, entity, description=None):
    """Log entity deletion"""
    return log_action(
        action='delete',
        entity_type=entity_type,
        entity_id=entity.id if hasattr(entity, 'id') else None,
        old_values=entity.to_dict() if hasattr(entity, 'to_dict') else None,
        description=description or f"Deleted {entity_type}"
    )


def log_export(entity_type, count, format_type, description=None):
    """Log data export"""
    return log_action(
        action='export',
        entity_type=entity_type,
        description=description or f"Exported {count} {entity_type} records as {format_type}"
    )


def get_recent_logs(limit=50, entity_type=None, user_id=None):
    """Get recent audit logs"""
    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    return query.limit(limit).all()
