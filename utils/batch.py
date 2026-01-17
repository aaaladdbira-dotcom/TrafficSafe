"""
Batch Operations Helper
=======================
Utilities for bulk create/update operations
"""

from extensions import db
from models.accident import Accident
from models.accident_report import AccidentReport
from utils.errors import ValidationError, DatabaseError
from datetime import datetime


class BatchAccidentCreator:
    """Bulk create accidents from list of dicts"""
    
    @staticmethod
    def validate_item(item: dict, index: int) -> dict:
        """Validate a single accident item"""
        required = ['location', 'severity']
        errors = []
        
        for field in required:
            if field not in item or not item[field]:
                errors.append(f"Item {index}: {field} is required")
        
        if item.get('severity') and item['severity'] not in ['low', 'medium', 'high']:
            errors.append(f"Item {index}: severity must be low/medium/high")
        
        if errors:
            raise ValidationError("Validation failed", {"errors": errors})
        
        return item
    
    @staticmethod
    def create_batch(items: list) -> dict:
        """
        Create multiple accidents
        
        Args:
            items: list of accident dicts
            
        Returns:
            dict with created_count and created_ids
            
        Raises:
            ValidationError if validation fails
            DatabaseError if database operation fails
        """
        if not items:
            raise ValidationError("items list cannot be empty")
        
        if len(items) > 100:
            raise ValidationError("Maximum 100 items per batch")
        
        # Validate all items first
        for i, item in enumerate(items):
            BatchAccidentCreator.validate_item(item, i)
        
        # Create accidents
        created = []
        try:
            for item in items:
                accident = Accident(
                    location=item.get('location'),
                    governorate=item.get('governorate') or item.get('location'),
                    delegation=item.get('delegation'),
                    severity=item.get('severity'),
                    cause=item.get('cause'),
                    occurred_at=item.get('occurred_at') or datetime.utcnow()
                )
                db.session.add(accident)
                created.append(accident)
            
            db.session.commit()
            
            return {
                "created_count": len(created),
                "created_ids": [a.id for a in created]
            }
        except Exception as e:
            db.session.rollback()
            raise DatabaseError(f"Batch create failed: {str(e)}")


class BatchReportCreator:
    """Bulk create accident reports from list of dicts"""
    
    @staticmethod
    def validate_item(item: dict, index: int) -> dict:
        """Validate a single report item"""
        required = ['accident_id', 'description']
        errors = []
        
        for field in required:
            if field not in item or not item[field]:
                errors.append(f"Item {index}: {field} is required")
        
        if errors:
            raise ValidationError("Validation failed", {"errors": errors})
        
        return item
    
    @staticmethod
    def create_batch(items: list, reporter_id: int) -> dict:
        """
        Create multiple accident reports
        
        Args:
            items: list of report dicts
            reporter_id: user ID of reporter
            
        Returns:
            dict with created_count and created_ids
            
        Raises:
            ValidationError if validation fails
            DatabaseError if database operation fails
        """
        if not items:
            raise ValidationError("items list cannot be empty")
        
        if len(items) > 100:
            raise ValidationError("Maximum 100 items per batch")
        
        # Validate all items first
        for i, item in enumerate(items):
            BatchReportCreator.validate_item(item, i)
        
        # Create reports
        created = []
        try:
            for item in items:
                # Verify accident exists
                accident = Accident.query.get(item['accident_id'])
                if not accident:
                    raise ValueError(f"Accident {item['accident_id']} not found")
                
                report = AccidentReport(
                    accident_id=item['accident_id'],
                    reporter_id=reporter_id,
                    description=item.get('description'),
                    status=item.get('status', 'pending')
                )
                db.session.add(report)
                created.append(report)
            
            db.session.commit()
            
            return {
                "created_count": len(created),
                "created_ids": [r.id for r in created]
            }
        except ValueError as e:
            db.session.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            db.session.rollback()
            raise DatabaseError(f"Batch create failed: {str(e)}")
