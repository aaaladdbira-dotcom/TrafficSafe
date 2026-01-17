"""
WebSocket Real-Time Updates
============================
Real-time accident notifications and live dashboard updates
Uses Flask-SocketIO for WebSocket communication
"""

from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import get_jwt_identity
import logging

logger = logging.getLogger(__name__)

# Active connections tracking
connected_users = {}
accident_subscribers = {}


def init_websocket(app, socketio):
    """Initialize WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        try:
            # Get JWT from request
            token = request.args.get('token')
            if token:
                # Store connection
                user_id = request.sid
                connected_users[user_id] = {
                    'sid': request.sid,
                    'connected_at': __import__('datetime').datetime.utcnow(),
                    'subscribed_to': []
                }
                logger.info(f"Client connected: {user_id}")
                emit('connection_response', {
                    'data': 'Connected to real-time server',
                    'sid': request.sid
                })
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnect"""
        user_id = request.sid
        if user_id in connected_users:
            del connected_users[user_id]
            logger.info(f"Client disconnected: {user_id}")
    
    @socketio.on('subscribe_accidents')
    def subscribe_accidents(data):
        """Subscribe to accident updates"""
        user_id = request.sid
        filters = data.get('filters', {})
        
        if user_id in connected_users:
            connected_users[user_id]['subscribed_to'].append({
                'type': 'accidents',
                'filters': filters
            })
            
            emit('subscription_confirmed', {
                'type': 'accidents',
                'filters': filters,
                'status': 'subscribed'
            })
            logger.info(f"User {user_id} subscribed to accidents with filters: {filters}")
    
    @socketio.on('subscribe_kpis')
    def subscribe_kpis():
        """Subscribe to KPI updates"""
        user_id = request.sid
        
        if user_id in connected_users:
            connected_users[user_id]['subscribed_to'].append({
                'type': 'kpis'
            })
            
            emit('subscription_confirmed', {
                'type': 'kpis',
                'status': 'subscribed'
            })
            logger.info(f"User {user_id} subscribed to KPIs")
    
    @socketio.on('unsubscribe')
    def unsubscribe(data):
        """Unsubscribe from updates"""
        user_id = request.sid
        sub_type = data.get('type')
        
        if user_id in connected_users:
            connected_users[user_id]['subscribed_to'] = [
                s for s in connected_users[user_id]['subscribed_to'] 
                if s.get('type') != sub_type
            ]
            
            emit('unsubscribed', {
                'type': sub_type,
                'status': 'unsubscribed'
            })
            logger.info(f"User {user_id} unsubscribed from {sub_type}")
    
    @socketio.on('ping')
    def handle_ping():
        """Heartbeat ping"""
        emit('pong', {'timestamp': __import__('datetime').datetime.utcnow().isoformat()})


def broadcast_new_accident(accident_data):
    """Broadcast new accident to all subscribers"""
    from flask_socketio import socketio as io
    
    try:
        # Notify all connected clients
        for user_id, user_info in connected_users.items():
            for subscription in user_info.get('subscribed_to', []):
                if subscription.get('type') == 'accidents':
                    # Check if accident matches filters
                    filters = subscription.get('filters', {})
                    if _matches_filters(accident_data, filters):
                        io.emit('new_accident', accident_data, room=user_info['sid'])
        
        logger.info(f"Broadcasted new accident to {len(connected_users)} users")
    except Exception as e:
        logger.error(f"Error broadcasting accident: {str(e)}")


def broadcast_kpi_update(kpi_data):
    """Broadcast KPI update to all subscribers"""
    from flask_socketio import socketio as io
    
    try:
        # Notify all connected clients
        for user_id, user_info in connected_users.items():
            for subscription in user_info.get('subscribed_to', []):
                if subscription.get('type') == 'kpis':
                    io.emit('kpi_update', kpi_data, room=user_info['sid'])
        
        logger.info(f"Broadcasted KPI update to {len(connected_users)} users")
    except Exception as e:
        logger.error(f"Error broadcasting KPI: {str(e)}")


def broadcast_live_stats(stats_data):
    """Broadcast live statistics update"""
    from flask_socketio import socketio as io
    
    try:
        for user_id, user_info in connected_users.items():
            io.emit('live_stats', stats_data, room=user_info['sid'])
    except Exception as e:
        logger.error(f"Error broadcasting stats: {str(e)}")


def _matches_filters(accident_data, filters):
    """Check if accident matches subscription filters"""
    if not filters:
        return True
    
    # Check governorate filter
    if 'governorate' in filters:
        if accident_data.get('governorate') != filters['governorate']:
            return False
    
    # Check severity filter
    if 'severity' in filters:
        if accident_data.get('severity') != filters['severity']:
            return False
    
    # Check cause filter
    if 'cause' in filters:
        if accident_data.get('cause') != filters['cause']:
            return False
    
    return True


def get_connected_users_count():
    """Get count of connected users"""
    return len(connected_users)


def get_subscriber_count(subscription_type):
    """Get count of subscribers to a specific type"""
    count = 0
    for user_info in connected_users.values():
        for sub in user_info.get('subscribed_to', []):
            if sub.get('type') == subscription_type:
                count += 1
    return count
