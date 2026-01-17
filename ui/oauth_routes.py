"""
OAuth Social Login Routes
=========================
Handles OAuth callbacks and user authentication/registration via social providers.

DEMO MODE: When OAuth credentials are not configured, uses simulated login for testing.
"""

import os
from flask import Blueprint, redirect, url_for, session, flash, request
from werkzeug.security import generate_password_hash
import secrets

from extensions import db
from models.user import User
from datetime import date

# Check if we're in demo mode (no real OAuth credentials)
def _provider_configured(var_name, placeholder=None):
    val = os.environ.get(var_name)
    if val is None:
        return False
    if placeholder:
        return val != placeholder
    return bool(val)

# Consider provider configured only when required credentials are set.
google_ok = _provider_configured('GOOGLE_CLIENT_ID', 'your-google-client-id') and _provider_configured('GOOGLE_CLIENT_SECRET', 'your-google-client-secret')
facebook_ok = _provider_configured('FACEBOOK_CLIENT_ID', 'your-facebook-app-id') and _provider_configured('FACEBOOK_CLIENT_SECRET', 'your-facebook-app-secret')
apple_ok = _provider_configured('APPLE_CLIENT_ID', 'your-apple-service-id') and _provider_configured('APPLE_CLIENT_SECRET')

# Demo mode if none of the providers are configured
DEMO_MODE = not (google_ok or facebook_ok or apple_ok)

oauth_ui = Blueprint("oauth_ui", __name__, url_prefix="/ui/oauth")

# Only import OAuth if not in demo mode
if not DEMO_MODE:
    from ui.oauth import oauth


def get_or_create_social_user(email, full_name, provider):
    """
    Find existing user by email or create a new one for social login.
    Returns the user object.
    """
    user = User.query.filter_by(email=email).first()
    
    if user:
        # User exists - just return them
        return user
    
    # Create new user with social login
    # Generate a random national_id placeholder for social users
    random_national_id = f"SOCIAL_{provider.upper()}_{secrets.token_hex(4).upper()}"
    
    user = User(
        full_name=full_name or email.split('@')[0],
        email=email,
        password_hash=generate_password_hash(secrets.token_urlsafe(32)),  # Random password
        role='citizen',
        user_type='citizen',
        national_id=random_national_id,
        gender='other',  # Default, user can update later
        # Some DB schemas may still enforce NOT NULL on date_of_birth.
        # Use a safe sentinel DOB for social users; run a migration later to allow NULLs.
        date_of_birth=date(1970, 1, 1),
        oauth_provider=provider,
    )
    
    db.session.add(user)
    db.session.commit()
    
    return user


def login_social_user(user):
    """Set up session for a social-authenticated user"""
    from flask_jwt_extended import create_access_token
    
    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "user_type": user.user_type,
        },
    )
    
    session["access_token"] = token
    session["role"] = user.role
    session["email"] = user.email
    session["dark_mode"] = user.dark_mode
    session["name"] = user.full_name


# ============================================
# DEMO MODE - Simulated OAuth for testing
# ============================================

@oauth_ui.route("/google")
def google_login():
    """Initiate Google OAuth flow"""
    if DEMO_MODE:
        # Demo mode - simulate Google login
        demo_email = "demo.google@example.com"
        demo_name = "Google Demo User"
        user = get_or_create_social_user(demo_email, demo_name, 'google')
        login_social_user(user)
        flash(f'Welcome, {user.full_name}! (Demo Mode)', 'success')
        return redirect(url_for('dashboard_ui.dashboard'))
    
    redirect_uri = url_for('oauth_ui.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_ui.route("/google/callback")
def google_callback():
    """Handle Google OAuth callback"""
    if DEMO_MODE:
        return redirect(url_for('dashboard_ui.dashboard'))
    
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            resp = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo')
            user_info = resp.json()
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not email:
            flash('Could not get email from Google', 'danger')
            return redirect(url_for('auth_ui.login'))
        
        user = get_or_create_social_user(email, name, 'google')
        login_social_user(user)
        
        flash(f'Welcome, {user.full_name}!', 'success')
        return redirect(url_for('dashboard_ui.dashboard'))
        
    except Exception as e:
        flash(f'Google login failed: {str(e)}', 'danger')
        return redirect(url_for('auth_ui.login'))


@oauth_ui.route("/facebook")
def facebook_login():
    """Initiate Facebook OAuth flow"""
    if DEMO_MODE:
        # Demo mode - simulate Facebook login
        demo_email = "demo.facebook@example.com"
        demo_name = "Facebook Demo User"
        user = get_or_create_social_user(demo_email, demo_name, 'facebook')
        login_social_user(user)
        flash(f'Welcome, {user.full_name}! (Demo Mode)', 'success')
        return redirect(url_for('dashboard_ui.dashboard'))
    
    redirect_uri = url_for('oauth_ui.facebook_callback', _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@oauth_ui.route("/facebook/callback")
def facebook_callback():
    """Handle Facebook OAuth callback"""
    if DEMO_MODE:
        return redirect(url_for('dashboard_ui.dashboard'))
    
    try:
        token = oauth.facebook.authorize_access_token()
        resp = oauth.facebook.get('me?fields=id,name,email')
        user_info = resp.json()
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not email:
            flash('Could not get email from Facebook. Please ensure email permission is granted.', 'danger')
            return redirect(url_for('auth_ui.login'))
        
        user = get_or_create_social_user(email, name, 'facebook')
        login_social_user(user)
        
        flash(f'Welcome, {user.full_name}!', 'success')
        return redirect(url_for('dashboard_ui.dashboard'))
        
    except Exception as e:
        flash(f'Facebook login failed: {str(e)}', 'danger')
        return redirect(url_for('auth_ui.login'))


@oauth_ui.route("/apple")
def apple_login():
    """Initiate Apple OAuth flow"""
    if DEMO_MODE:
        # Demo mode - simulate Apple login
        demo_email = "demo.apple@example.com"
        demo_name = "Apple Demo User"
        user = get_or_create_social_user(demo_email, demo_name, 'apple')
        login_social_user(user)
        flash(f'Welcome, {user.full_name}! (Demo Mode)', 'success')
        return redirect(url_for('dashboard_ui.dashboard'))
    
    redirect_uri = url_for('oauth_ui.apple_callback', _external=True)
    return oauth.apple.authorize_redirect(redirect_uri)


@oauth_ui.route("/apple/callback", methods=['GET', 'POST'])
def apple_callback():
    """Handle Apple OAuth callback"""
    if DEMO_MODE:
        return redirect(url_for('dashboard_ui.dashboard'))
    
    try:
        token = oauth.apple.authorize_access_token()
        user_data = request.form.get('user')
        
        from authlib.jose import jwt as jose_jwt
        id_token = token.get('id_token')
        
        if id_token:
            claims = jose_jwt.decode(id_token, None, claims_options={"verify_signature": False})
            email = claims.get('email')
        else:
            email = None
        
        name = None
        if user_data:
            import json
            user_json = json.loads(user_data)
            first_name = user_json.get('name', {}).get('firstName', '')
            last_name = user_json.get('name', {}).get('lastName', '')
            name = f"{first_name} {last_name}".strip()
        
        if not email:
            flash('Could not get email from Apple', 'danger')
            return redirect(url_for('auth_ui.login'))
        
        user = get_or_create_social_user(email, name, 'apple')
        login_social_user(user)
        
        flash(f'Welcome, {user.full_name}!', 'success')
        return redirect(url_for('dashboard_ui.dashboard'))
        
    except Exception as e:
        flash(f'Apple login failed: {str(e)}', 'danger')
        return redirect(url_for('auth_ui.login'))
