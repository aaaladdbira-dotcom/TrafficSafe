"""
Query Parameter Validation Helpers
===================================
Validates and sanitizes API query parameters
"""

from flask import request
from utils.errors import ValidationError
from typing import Optional, Tuple


class PaginationValidator:
    """Validates pagination parameters"""
    
    DEFAULT_PAGE = 1
    DEFAULT_PER_PAGE = 20
    MAX_PER_PAGE = 100
    
    @staticmethod
    def validate() -> Tuple[int, int]:
        """
        Validate page and per_page from request.args
        
        Returns:
            (page, per_page) - validated positive integers
            
        Raises:
            ValidationError if validation fails
        """
        try:
            page = request.args.get('page', PaginationValidator.DEFAULT_PAGE, type=int)
            per_page = request.args.get('per_page', PaginationValidator.DEFAULT_PER_PAGE, type=int)
        except (ValueError, TypeError):
            raise ValidationError("page and per_page must be integers")
        
        if page < 1:
            raise ValidationError("page must be >= 1")
        
        if per_page < 1:
            raise ValidationError("per_page must be >= 1")
        
        if per_page > PaginationValidator.MAX_PER_PAGE:
            raise ValidationError(
                f"per_page must be <= {PaginationValidator.MAX_PER_PAGE}",
                {"max_per_page": PaginationValidator.MAX_PER_PAGE}
            )
        
        return page, per_page


class SortValidator:
    """Validates sort parameters"""
    
    @staticmethod
    def validate(allowed_fields: list) -> Tuple[Optional[str], str]:
        """
        Validate sort_by and sort_order from request.args
        
        Args:
            allowed_fields: list of field names allowed for sorting
            
        Returns:
            (sort_by, sort_order) - validated field and direction
            
        Raises:
            ValidationError if validation fails
        """
        sort_by = request.args.get('sort_by', None)
        sort_order = request.args.get('sort_order', 'asc').lower()
        
        if sort_order not in ('asc', 'desc'):
            raise ValidationError("sort_order must be 'asc' or 'desc'")
        
        if sort_by and sort_by not in allowed_fields:
            raise ValidationError(
                f"sort_by must be one of: {', '.join(allowed_fields)}",
                {"allowed_fields": allowed_fields}
            )
        
        return sort_by, sort_order


class DateRangeValidator:
    """Validates date range parameters"""
    
    @staticmethod
    def validate() -> Tuple[Optional[str], Optional[str]]:
        """
        Validate start_date and end_date from request.args (ISO format)
        
        Returns:
            (start_date, end_date) - validated ISO date strings or None
            
        Raises:
            ValidationError if validation fails
        """
        from datetime import datetime
        
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        if start_date:
            try:
                datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                raise ValidationError("start_date must be ISO format (YYYY-MM-DD or ISO-8601)")
        
        if end_date:
            try:
                datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                raise ValidationError("end_date must be ISO format (YYYY-MM-DD or ISO-8601)")
        
        if start_date and end_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if start > end:
                raise ValidationError("start_date must be <= end_date")
        
        return start_date, end_date


class FilterValidator:
    """Validates filter parameters"""
    
    @staticmethod
    def validate_enum(param_name: str, allowed_values: list) -> Optional[str]:
        """
        Validate that a query parameter is one of allowed values
        
        Args:
            param_name: name of parameter to check in request.args
            allowed_values: list of valid values
            
        Returns:
            validated value or None if not provided
            
        Raises:
            ValidationError if invalid
        """
        value = request.args.get(param_name, None)
        
        if value and value not in allowed_values:
            raise ValidationError(
                f"{param_name} must be one of: {', '.join(allowed_values)}",
                {param_name: allowed_values}
            )
        
        return value
    
    @staticmethod
    def validate_string(param_name: str, max_length: int = 255, required: bool = False) -> Optional[str]:
        """
        Validate a string parameter
        
        Args:
            param_name: name of parameter to check in request.args
            max_length: maximum allowed string length
            required: whether parameter is required
            
        Returns:
            validated string or None
            
        Raises:
            ValidationError if invalid
        """
        value = request.args.get(param_name, None)
        
        if required and not value:
            raise ValidationError(f"{param_name} is required")
        
        if value and len(value) > max_length:
            raise ValidationError(
                f"{param_name} must be <= {max_length} characters",
                {"max_length": max_length}
            )
        
        return value
