# Quick Reference: Testing Real OAuth Locally

## Checklist Before Testing

- [ ] All OAuth credentials are in `.env` (not placeholder values)
- [ ] `.env` file is in project root (same folder as `app.py`)
- [ ] You ran `pip install python-dotenv`
- [ ] Your app is running with `python app.py`
- [ ] Redirect URIs are registered in each provider's console

## Test URLs

| Provider | Login URL | Callback URL |
|----------|-----------|--------------|
| **Google** | `http://127.0.0.1:5001/ui/oauth/google` | `http://127.0.0.1:5001/ui/oauth/google/callback` |
| **Facebook** | `http://127.0.0.1:5001/ui/oauth/facebook` | `http://127.0.0.1:5001/ui/oauth/facebook/callback` |
| **Apple** | `http://127.0.0.1:5001/ui/oauth/apple` | `http://127.0.0.1:5001/ui/oauth/apple/callback` |

## Testing Steps

### 1. Verify `.env` is Loaded
```bash
# In Python REPL (while app is running or in same directory)
import os
from dotenv import load_dotenv
load_dotenv()

print(f"GOOGLE_CLIENT_ID: {os.environ.get('GOOGLE_CLIENT_ID')}")
print(f"FACEBOOK_CLIENT_ID: {os.environ.get('FACEBOOK_CLIENT_ID')}")
print(f"APPLE_CLIENT_ID: {os.environ.get('APPLE_CLIENT_ID')}")
```

All three should show real credentials, NOT placeholders.

### 2. Test Google Login Flow

**Step 1**: Go to login page
```
http://127.0.0.1:5001/ui/login
```

**Step 2**: Click "Login with Google"

**Step 3**: Expected behavior:
- [ ] You are redirected to `https://accounts.google.com/...` (Google's consent screen)
- [ ] NOT staying on your app with a "Demo Mode" message
- [ ] You see a login prompt or consent request

**Step 4**: Sign in with your Google account
- [ ] Grant all requested permissions
- [ ] You should be redirected back to your app

**Step 5**: Verify login success
- [ ] You see a welcome message
- [ ] You are on the dashboard page
- [ ] Your email appears in the navbar (or user menu)

**Step 6**: Check database
```bash
# Open your SQLite database
# Check users table - you should see a new user with your Google email
```

### 3. Test Facebook Login Flow

Same as Google, but:
1. Click "Login with Facebook"
2. Should redirect to `https://www.facebook.com/login.php?...`
3. Sign in with your Facebook account
4. Grant email permission (this is required)
5. Verify you're logged in

### 4. Test Apple Login Flow

Same as Google, but:
1. Click "Login with Apple"
2. Should redirect to `https://appleid.apple.com/auth/authorize`
3. Sign in with your Apple ID
4. Grant requested permissions
5. Verify you're logged in

---

## Demo Mode Indicator

If you still see this message in your Flask logs:
```
DEMO_MODE = True
```

Then OAuth credentials are NOT properly configured. Check:
1. Do you have a `.env` file in project root?
2. Does `.env` have real values (not placeholders)?
3. Did you restart your Flask app after adding `.env`?
4. Are there any typos in credential values?

---

## Common Issues & Quick Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Still showing "Demo Mode" login | `.env` not loaded or has placeholders | Verify `.env` exists with real credentials, restart app |
| "Redirect URI mismatch" error | URI doesn't match provider console | Copy exact URI from your Flask logs, update provider console |
| "Invalid Client ID" error | Credentials are wrong | Double-check credentials in `.env`, copy from provider console again |
| "Email not returned" error | User didn't grant email permission | Tell user to grant email permission, or remove app and retry |
| Blank page after "Click button" | OAuth provider integration failing | Check Flask app logs for errors, verify credentials |

---

## How to Read Flask Logs

When you run `python app.py`, watch for:

```
WARNING: in function 'create_app' - DEMO_MODE: OAuth credentials not configured. Using demo/test login.
```

This means demo mode is active. Fix by adding real credentials to `.env`.

Or if you see:

```
* Running on http://127.0.0.1:5001
```

The app is running and ready for testing.

---

## Browser Console Debugging

If redirect isn't working:

1. **Open Chrome Developer Tools**: `F12`
2. **Go to Console tab**
3. **Look for JavaScript errors**
4. **Check Network tab**:
   - Click "Login with Google"
   - Look for requests starting with `accounts.google.com`
   - If no redirect is happening, the button might not be linked correctly

---

## Production vs Development

| Aspect | Development (Local) | Production |
|--------|---------------------|------------|
| **Domain** | `127.0.0.1:5001` | `yourdomain.com` |
| **Protocol** | `http://` | `https://` |
| **Redirect URI** | `http://127.0.0.1:5001/ui/oauth/...` | `https://yourdomain.com/ui/oauth/...` |
| **Database** | SQLite (local file) | PostgreSQL/MySQL (remote) |
| **Secrets** | In `.env` (not in git) | In environment manager (AWS Secrets, GCP Secret Manager) |

---

## Sample Test Accounts

Create test accounts with each provider for realistic testing:
- **Google**: Create a test Gmail account
- **Facebook**: Create a Facebook test account
- **Apple**: Use your real Apple ID (no test account needed)

---

## Success Indicators

✅ Real OAuth is working when:
1. Clicking "Login with [Provider]" redirects to provider's site
2. You authenticate with your real account
3. You're redirected back with a success message
4. User is created in the database with correct email
5. JWT token is issued and stored in session

---

## Getting Help

If something doesn't work:

1. **Check `.env` file**: `cat .env` or open in editor
2. **Check Flask logs**: Look for errors when you start the app
3. **Check redirect URIs**: Must match EXACTLY in provider console
4. **Verify credentials**: Copy fresh from provider console
5. **Restart app**: Kill Flask and run again
6. **Clear browser cookies**: Sometimes old session data causes issues

Run:
```bash
# Windows
del traffic.db
python app.py

# Linux/Mac
rm traffic.db
python app.py
```

This resets the local database and restarts fresh.
