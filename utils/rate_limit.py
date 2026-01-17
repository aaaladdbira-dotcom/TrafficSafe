"""
Rate Limiting Service
=====================
Protect API endpoints from abuse
"""

import time
from functools import wraps
from collections import defaultdict
from flask import request, jsonify, g


class RateLimiter:
    """In-memory rate limiter"""
    
    def __init__(self):
        # Store: { key: [(timestamp, count)] }
        self.requests = defaultdict(list)
        self.blocked = {}  # Temporarily blocked IPs
    
    def _clean_old_requests(self, key, window):
        """Remove requests older than the window"""
        now = time.time()
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key]
            if now - ts < window
        ]
    
    def _get_request_count(self, key, window):
        """Count requests within the window"""
        self._clean_old_requests(key, window)
        return sum(count for _, count in self.requests[key])
    
    def is_rate_limited(self, key, limit, window):
        """
        Check if a key is rate limited.
        
        Args:
            key: Identifier (IP, user ID, etc.)
            limit: Max requests allowed
            window: Time window in seconds
        
        Returns:
            (is_limited, remaining, retry_after)
        """
        # Check if blocked
        if key in self.blocked:
            block_until = self.blocked[key]
            if time.time() < block_until:
                return True, 0, int(block_until - time.time())
            else:
                del self.blocked[key]
        
        count = self._get_request_count(key, window)
        
        if count >= limit:
            return True, 0, window
        
        return False, limit - count, 0
    
    def record_request(self, key):
        """Record a request"""
        now = time.time()
        self.requests[key].append((now, 1))
    
    def block(self, key, duration):
        """Temporarily block a key"""
        self.blocked[key] = time.time() + duration


# Global rate limiter
limiter = RateLimiter()


# Default limits
RATE_LIMITS = {
    'default': (100, 60),      # 100 requests per minute
    'auth': (5, 60),           # 5 auth attempts per minute
    'api': (60, 60),           # 60 API calls per minute
    'search': (30, 60),        # 30 searches per minute
    'export': (10, 60),        # 10 exports per minute
    'upload': (5, 60),         # 5 uploads per minute
}


def get_rate_limit_key():
    """Get rate limit key from request"""
    # Use user ID if authenticated, otherwise IP
    user_id = getattr(g, 'user_id', None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{request.remote_addr}"


def rate_limit(limit_type='default', limit=None, window=None):
    """
    Rate limiting decorator.
    
    Usage:
        @rate_limit()  # Use default limits
        @rate_limit('auth')  # Use auth limits
        @rate_limit(limit=10, window=60)  # Custom limits
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = get_rate_limit_key()
            
            # Get limits
            if limit and window:
                max_requests, time_window = limit, window
            else:
                max_requests, time_window = RATE_LIMITS.get(
                    limit_type, RATE_LIMITS['default']
                )
            
            # Check rate limit
            is_limited, remaining, retry_after = limiter.is_rate_limited(
                key, max_requests, time_window
            )
            
            # Add rate limit headers
            response_headers = {
                'X-RateLimit-Limit': str(max_requests),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Window': str(time_window)
            }
            
            if is_limited:
                response = jsonify({
                    'error': 'Too many requests',
                    'message': f'Rate limit exceeded. Try again in {retry_after} seconds.',
                    'retry_after': retry_after
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(retry_after)
                for header, value in response_headers.items():
                    response.headers[header] = value
                return response
            
            # Record request
            limiter.record_request(key)
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Add headers to successful response
            if hasattr(response, 'headers'):
                for header, value in response_headers.items():
                    response.headers[header] = value
            
            return response
        
        return decorated_function
    return decorator


def check_rate_limit(limit_type='default'):
    """Check rate limit without blocking (for manual checks)"""
    key = get_rate_limit_key()
    max_requests, time_window = RATE_LIMITS.get(limit_type, RATE_LIMITS['default'])
    return limiter.is_rate_limited(key, max_requests, time_window)
