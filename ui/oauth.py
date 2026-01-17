"""
OAuth Social Login Configuration
================================
This module handles OAuth authentication with Google, Apple, and Facebook.

To enable social login, you need to:
1. Create OAuth apps on each provider's developer console
2. Set the environment variables with your credentials
3. Configure the redirect URIs in each provider's console

Environment Variables Required:
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
- APPLE_CLIENT_ID, APPLE_CLIENT_SECRET, APPLE_TEAM_ID, APPLE_KEY_ID
- FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET
"""

import os
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

oauth = OAuth()

# ============================================
# GOOGLE OAuth Configuration
# ============================================
# Create credentials at: https://console.cloud.google.com/apis/credentials
# Redirect URI: http://localhost:5001/ui/oauth/google/callback

google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')

if google_client_id and google_client_secret:
    oauth.register(
        name='google',
        client_id=google_client_id,
        client_secret=google_client_secret,
        authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
        access_token_url='https://oauth2.googleapis.com/token',
        userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
        client_kwargs={
            'scope': 'email profile'
        }
    )

# ============================================
# FACEBOOK OAuth Configuration
# ============================================
# Create app at: https://developers.facebook.com/apps/
# Redirect URI: http://localhost:5001/ui/oauth/facebook/callback

oauth.register(
    name='facebook',
    client_id=os.environ.get('FACEBOOK_CLIENT_ID', 'your-facebook-app-id'),
    client_secret=os.environ.get('FACEBOOK_CLIENT_SECRET', 'your-facebook-app-secret'),
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    api_base_url='https://graph.facebook.com/',
    client_kwargs={
        'scope': 'email public_profile'
    }
)

# ============================================
# APPLE OAuth Configuration
# ============================================
# Create credentials at: https://developer.apple.com/account/resources/identifiers/list/serviceId
# Redirect URI: http://localhost:5001/ui/oauth/apple/callback

oauth.register(
    name='apple',
    client_id=os.environ.get('APPLE_CLIENT_ID', 'your-apple-service-id'),
    client_secret=os.environ.get('APPLE_CLIENT_SECRET', ''),  # Generated JWT
    authorize_url='https://appleid.apple.com/auth/authorize',
    access_token_url='https://appleid.apple.com/auth/token',
    client_kwargs={
        'scope': 'name email',
        'response_mode': 'form_post'
    }
)


def init_oauth(app):
    """Initialize OAuth with Flask app"""
    oauth.init_app(app)
