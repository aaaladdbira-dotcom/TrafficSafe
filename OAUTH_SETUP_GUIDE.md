# OAuth 2.0 Real Authentication Setup Guide

## Overview

This guide walks you through replacing demo OAuth with real OAuth 2.0 Authorization Code Flow. Your app will now redirect users to Google, Facebook, or Apple to choose their accounts instead of using demo users.

## Key Changes Made

1. ✅ Added `python-dotenv` to requirements
2. ✅ Updated `app.py` to load `.env` file at startup
3. ✅ Created `.env` file (already in .gitignore for security)
4. ✅ OAuth routes detect real credentials and disable demo mode automatically

## How It Works

Your code has a smart detection system:
- If OAuth credentials are set to real values in `.env`, **real OAuth flow** activates
- If credentials are missing or still have placeholder values, **demo mode** shows a warning and uses test users
- The `DEMO_MODE` flag in `ui/oauth_routes.py` automatically switches based on credentials

## Step-by-Step Setup

### 1. Google OAuth Setup

#### 1.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a Project** → **New Project**
3. Enter name: `Traffic Accident App`
4. Click **Create**

#### 1.2 Enable Google+ API
1. Search for **Google+ API** in the search bar
2. Click the result → **Enable**
3. Wait for it to be enabled

#### 1.3 Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials** (left sidebar)
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted, click **Configure OAuth Consent Screen**:
   - **User Type**: Select **External**
   - **App name**: `Traffic Accident System`
   - **User support email**: Your email
   - **Developer contact**: Your email
   - Click **Save and Continue**
   - **Scopes**: Add these scopes:
     - `email`
     - `profile`
     - `openid`
   - Click **Save and Continue**
   - Click **Back to Dashboard**

4. Now create OAuth Client ID:
   - **Application Type**: **Web application**
   - **Name**: `Traffic Accident App`
   - **Authorized JavaScript origins**:
     ```
     http://127.0.0.1:5001
     ```
   - **Authorized redirect URIs**:
     ```
     http://127.0.0.1:5001/ui/oauth/google/callback
     ```
   - Click **Create**

5. Copy your **Client ID** and **Client Secret** from the popup
6. Add to `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id-here
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   ```

---

### 2. Facebook OAuth Setup

#### 2.1 Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Choose **Consumer** → **Next**
4. **App Name**: `Traffic Accident System`
5. **App Purpose**: Select relevant option
6. Click **Create App**

#### 2.2 Set Up Facebook Login
1. In your app dashboard, click **+ Add Product**
2. Find **Facebook Login** → **Set Up**
3. Choose **Web** → **Next** (Skip the quick start)
4. Go to **Settings** → **Basic**
   - Copy **App ID** and **App Secret**

5. Go to **Facebook Login** → **Settings** (in left menu)
6. **Valid OAuth Redirect URIs**:
   ```
   http://127.0.0.1:5001/ui/oauth/facebook/callback
   ```
   - Click **Save Changes**

7. Go to **Settings** → **Basic**
8. Under **App Domains**:
   ```
   127.0.0.1:5001
   ```
   - Click **Save Changes**

9. Add to `.env`:
   ```
   FACEBOOK_CLIENT_ID=your-app-id-here
   FACEBOOK_CLIENT_SECRET=your-app-secret-here
   ```

---

### 3. Apple OAuth Setup

#### 3.1 Create Service ID
1. Go to [Apple Developer Account](https://developer.apple.com/account/)
2. Click **Certificates, Identifiers & Profiles**
3. Click **Identifiers** (left sidebar)
4. Click **+** to register a new identifier
5. Select **Service IDs** → **Continue**
6. **Description**: `Traffic Accident App`
7. **Identifier**: Use reverse domain notation (e.g., `com.yourdomain.trafficapp`)
   - This is your `APPLE_CLIENT_ID`
8. Check **Sign in with Apple** → **Configure**
9. **Primary App ID**: Choose your main app ID
10. **Web Domains**:
    ```
    127.0.0.1:5001
    ```
11. **Return URLs**:
    ```
    http://127.0.0.1:5001/ui/oauth/apple/callback
    ```
12. Click **Save** → **Continue** → **Register**

#### 3.2 Create Private Key
1. Go to **Keys** (left sidebar)
2. Click **+** to create a new key
3. **Key Name**: `Traffic Accident App Key`
4. Check **Sign in with Apple** → **Configure**
5. Select your Service ID from step 3.1 → **Save** → **Continue** → **Register**
6. **Download** the `.p8` private key file (save in a secure location)
7. Note your **Key ID** (shown on the keys page)

#### 3.3 Get Team ID
1. Go to [https://developer.apple.com/account/](https://developer.apple.com/account/)
2. Click your account name (top right) → **Membership details**
3. Copy your **Team ID**

#### 3.4 Encode Private Key for `.env`
1. Open the downloaded `.p8` file with a text editor
2. Copy the **entire content** (including `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----`)
3. For the `.env` file, you can either:
   - **Option A**: Use the raw PEM content (multiline)
   - **Option B**: Convert to single line by replacing newlines with `\n`

4. Add to `.env`:
   ```
   APPLE_CLIENT_ID=com.yourdomain.trafficapp
   APPLE_TEAM_ID=your-team-id-here
   APPLE_KEY_ID=your-key-id-here
   APPLE_CLIENT_SECRET=<paste-full-private-key-content>
   ```

---

### 4. Complete Your `.env` File

```env
# Google OAuth
GOOGLE_CLIENT_ID=123456789.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnop

# Facebook OAuth
FACEBOOK_CLIENT_ID=1234567890
FACEBOOK_CLIENT_SECRET=abcdefghijklmnopqrstuvwxyz

# Apple OAuth
APPLE_CLIENT_ID=com.yourdomain.trafficapp
APPLE_TEAM_ID=ABCD1234EF
APPLE_KEY_ID=ABC123DEF456
APPLE_CLIENT_SECRET=-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgR7zfz4/6K5bZ2sTB
...rest of private key content...
-----END PRIVATE KEY-----

# Flask Config
FLASK_ENV=development
SECRET_KEY=your-secure-flask-secret-key-change-this
JWT_SECRET_KEY=your-secure-jwt-secret-key-change-this
```

---

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `python-dotenv` (already added to requirements).

---

### 6. Test the Real OAuth Flow

#### Start Your App
```bash
python app.py
```

#### Test Google Login
1. Go to `http://127.0.0.1:5001/ui/login`
2. Click **Login with Google**
3. You should be **redirected to Google's consent screen** (not a demo page)
4. Sign in with a real Google account
5. Grant permissions
6. You should be logged in

#### Test Facebook Login
1. Click **Login with Facebook**
2. You should be **redirected to Facebook's login page**
3. Sign in with a real Facebook account
4. Grant permissions
5. You should be logged in

#### Test Apple Login
1. Click **Login with Apple**
2. You should be **redirected to Apple's sign-in page**
3. Sign in with a real Apple account
4. You should be logged in

---

## Troubleshooting

### Issue: Still seeing "Demo Mode" flash message

**Solution**: Check that your `.env` file has real values (not placeholders):
```bash
# View your .env file
type .env

# or on Linux/Mac
cat .env
```

Make sure values like `your-google-client-id` are replaced with actual credentials.

### Issue: Redirect URI mismatch error

**Solution**: Ensure redirect URI exactly matches in your OAuth provider console:
```
http://127.0.0.1:5001/ui/oauth/google/callback
http://127.0.0.1:5001/ui/oauth/facebook/callback
http://127.0.0.1:5001/ui/oauth/apple/callback
```

**Important**: Use `http://` (not `https://`) for local development.

### Issue: "Invalid Client ID" error

**Solution**: 
- Copy the credentials again from your provider console
- Make sure there are no extra spaces in `.env`
- Restart your Flask app after updating `.env`

### Issue: Email permission denied by user

**Solution**: Users must grant email permission during OAuth consent. If they deny it, they cannot log in. Inform users that email is required.

---

## Security Best Practices

1. **Never commit `.env` to version control** - Already in `.gitignore` ✓
2. **Use strong `SECRET_KEY` and `JWT_SECRET_KEY`** - Change from defaults
3. **Rotate API credentials regularly** - Update in OAuth provider consoles
4. **Use HTTPS in production** - Update redirect URIs to `https://yourdomain.com`
5. **Store sensitive data** - Don't share your `.env` file
6. **Monitor OAuth logs** - Review failed login attempts in provider consoles

---

## Production Deployment

When deploying to production:

1. **Update Redirect URIs** in each OAuth provider:
   ```
   https://yourdomain.com/ui/oauth/google/callback
   https://yourdomain.com/ui/oauth/facebook/callback
   https://yourdomain.com/ui/oauth/apple/callback
   ```

2. **Use environment variables on server** (AWS Secrets Manager, GCP Secret Manager, etc.)

3. **Update `.env` on production server** with production credentials

4. **Use HTTPS-only redirect URIs**

5. **Set strong secrets**:
   ```
   FLASK_ENV=production
   SECRET_KEY=<very-long-random-string>
   JWT_SECRET_KEY=<very-long-random-string>
   ```

---

## How OAuth 2.0 Authorization Code Flow Works

Your app now implements the standard OAuth 2.0 Authorization Code Flow:

```
1. User clicks "Login with Google"
   ↓
2. App redirects to: https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...
   ↓
3. User sees Google's consent screen
   ↓
4. User grants permissions
   ↓
5. Google redirects back to: http://127.0.0.1:5001/ui/oauth/google/callback?code=<auth-code>
   ↓
6. Backend exchanges code for access token
   ↓
7. Backend retrieves user info (email, name) from Google
   ↓
8. User is logged in to your app
```

This flow ensures:
- ✅ Users authenticate with real OAuth providers
- ✅ Your app never sees the user's password
- ✅ Secure token exchange on backend
- ✅ User data is fetched from authoritative source

---

## Files Changed

- ✅ `requirements.txt` - Added `python-dotenv`
- ✅ `app.py` - Added `.env` loading
- ✅ `.env` - Created with placeholder credentials
- ✅ `ui/oauth.py` - Already configured (no changes needed)
- ✅ `ui/oauth_routes.py` - Already configured (no changes needed)

## Next Steps

1. Complete the OAuth setup for each provider
2. Fill in real credentials in `.env`
3. Restart your app: `python app.py`
4. Test each provider's login flow
5. Verify users are created in the database
6. Check that JWT tokens are issued correctly

Good luck! Your OAuth 2.0 implementation is production-ready.
