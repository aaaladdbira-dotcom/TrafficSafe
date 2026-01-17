"""
Standardized Error Response System
===================================
Provides consistent error formatting across all API endpoints
"""

from flask import jsonify
from typing import Optional, Dict, Any


class APIError(Exception):
    """Base API error with standardized response format"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to JSON-serializable dict"""
        response = {
            "error": self.message,
            "code": self.code,
            "status": self.status_code
        }
        if self.details:
            response["details"] = self.details
        return response
    
    def to_response(self):
        """Convert to Flask response"""
        return jsonify(self.to_dict()), self.status_code


# ============ ERROR DEFINITIONS ============

class ValidationError(APIError):
    """Request validation failed (400)"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class NotFoundError(APIError):
    """Resource not found (404)"""
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404
        )


class UnauthorizedError(APIError):
    """Authentication failed (401)"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401
        )


class ForbiddenError(APIError):
    """User lacks permission (403)"""
    def __init__(self, message: str = "Forbidden", action: Optional[str] = None):
        if action:
            message = f"Forbidden: {action}"
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403
        )


class ConflictError(APIError):
    """Resource conflict (409)"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409
        )


class RateLimitError(APIError):
    """Rate limit exceeded (429)"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )


class DatabaseError(APIError):
    """Database operation failed (500)"""
    def __init__(self, message: str = "Database error"):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500
        )


# ============ SUCCESS RESPONSES ============

def success_response(data: Any = None, message: str = "Success", status_code: int = 200):
    """Return standardized success response"""
    response = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code


def paginated_response(items: list, page: int, per_page: int, total: int, message: str = "Success"):
    """Return standardized paginated response"""
    total_pages = (total + per_page - 1) // per_page
    return jsonify({
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages
        }
    }), 200
