"""
Two-Factor Authentication Service
=================================
Optional 2FA for admin accounts
"""

import os
import secrets
import time
import hashlib
from datetime import datetime, timedelta
from extensions import db


class TwoFactorCode(db.Model):
    """Stores temporary 2FA codes"""
    __tablename__ = "two_factor_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code_hash = db.Column(db.String(64), nullable=False)  # SHA256 hash of code
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)
    
    def is_valid(self, code):
        """Check if code is valid and not expired"""
        if self.used:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return self.code_hash == hashlib.sha256(code.encode()).hexdigest()


class TwoFactorService:
    """Service for handling 2FA operations"""
    
    CODE_LENGTH = 6
    CODE_EXPIRY_MINUTES = 10
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(TwoFactorService.CODE_LENGTH)])
    
    @staticmethod
    def create_code(user_id):
        """Create and store a new 2FA code for a user"""
        # Invalidate existing codes
        TwoFactorCode.query.filter_by(user_id=user_id, used=False).update({'used': True})
        
        # Generate new code
        code = TwoFactorService.generate_code()
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        # Store hashed code
        two_factor = TwoFactorCode(
            user_id=user_id,
            code_hash=code_hash,
            expires_at=datetime.utcnow() + timedelta(minutes=TwoFactorService.CODE_EXPIRY_MINUTES)
        )
        
        db.session.add(two_factor)
        db.session.commit()
        
        return code
    
    @staticmethod
    def verify_code(user_id, code):
        """Verify a 2FA code"""
        # Find valid code for user
        two_factor = TwoFactorCode.query.filter_by(
            user_id=user_id,
            used=False
        ).order_by(TwoFactorCode.created_at.desc()).first()
        
        if not two_factor:
            return False, "No verification code found"
        
        if datetime.utcnow() > two_factor.expires_at:
            return False, "Code has expired"
        
        if not two_factor.is_valid(code):
            return False, "Invalid code"
        
        # Mark as used
        two_factor.used = True
        db.session.commit()
        
        return True, "Code verified"
    
    @staticmethod
    def cleanup_expired():
        """Remove expired codes"""
        TwoFactorCode.query.filter(
            TwoFactorCode.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
    
    @staticmethod
    def send_code_email(user):
        """Generate and send 2FA code via email"""
        from utils.email_service import email_service
        
        code = TwoFactorService.create_code(user.id)
        email_service.send_2fa_code(user.email, user.full_name, code)
        
        return True


# Check if 2FA is required for a user
def requires_2fa(user):
    """Check if user requires 2FA"""
    # 2FA for admins and government users
    return user.role in ['admin', 'government']
