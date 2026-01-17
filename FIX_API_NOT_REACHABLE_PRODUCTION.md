# Fix: API Not Reachable on Production

## Problem
When visiting `https://trafficsafe.onrender.com/ui/accidents`, the page displays:
```
API not reachable
```

This is because the UI was trying to reach the API using hardcoded URLs or incorrect configuration, which fails in a production environment where the API and UI are on the same origin.

## Root Cause Analysis
The previous fix attempted to use an explicit `API_URL` environment variable, but:
1. On Render, the environment variable was never set
2. The fallback default was `http://localhost:5001` which doesn't work on production
3. API and UI are both running on the same Render service (`https://trafficsafe.onrender.com`)

The correct approach is to use **same-origin requests** by default (empty API_URL), so the browser makes requests to the same host without needing explicit configuration.

## Solution Implemented

### 1. Updated `app.py` (Line 120-123)
Changed the API_URL default from `http://localhost:5001` to an empty string:

**Before:**
```python
app.config["API_URL"] = os.environ.get("API_URL", "http://localhost:5001")
```

**After:**
```python
# API_URL for UI to communicate with API layer
# Default to empty string (relative URLs) so it uses same origin on production
# Can be overridden with API_URL env var for separate API servers
app.config["API_URL"] = os.environ.get("API_URL", "")
```

### 2. Updated `ui/accidents_ui.py`
Added a smart helper function `get_api_url()` that:
- Uses an explicit `API_URL` if configured (for separate API servers)
- Uses the **current request scheme and host** by default (for same-origin requests)
- Works on both localhost and production

**New helper function (Lines 9-18):**
```python
def get_api_url(endpoint):
    """Build absolute API URL.
    
    If API_URL is configured, use it as base.
    Otherwise, use current request host (for same-origin requests on production).
    """
    api_base = current_app.config.get('API_URL', '')
    
    if api_base:
        # Explicitly configured API URL
        return f"{api_base}{endpoint}"
    else:
        # Same-origin: use current request scheme/host
        return f"{request.scheme}://{request.host}{endpoint}"
```

**Updated all 9 API calls to use this helper:**
- Line 33: `edit_accident()` 
- Line 73: `accident_detail()`
- Line 120: `accidents()` - filters endpoint
- Line 145: `accidents()` - main list endpoint
- Line 289: `accidents_data()` - AJAX proxy
- Line 334: `accidents_filters_proxy()`
- Line 366: `accidents_export_proxy()`
- Line 393: `accidents_batches_proxy()`
- Line 418: `clear_imports()`

## How It Works

### On Production (Render)
1. User visits: `https://trafficsafe.onrender.com/ui/accidents`
2. API_URL env var is not set (defaults to empty string)
3. UI makes request using: `https://trafficsafe.onrender.com/api/v1/accidents`
4. Since both UI and API are on Render, this **same-origin request works perfectly**

### On Local Development
1. User visits: `http://localhost:5001/ui/accidents`
2. API_URL env var is not set (defaults to empty string)
3. UI makes request using: `http://localhost:5001/api/v1/accidents`
4. Works correctly since they're on the same origin

### With Separate API Server (Optional)
If you deploy the API on a different server:
1. Set `API_URL=https://api.example.com` on the UI service
2. UI makes requests to: `https://api.example.com/api/v1/accidents`

## Why This Is Better

| Aspect | Previous Fix | Current Fix |
|--------|-------------|-----------|
| Production Default | ❌ Hardcoded localhost | ✅ Uses same origin |
| Local Dev | ✓ Works | ✓ Works |
| Separate API Server | ❌ Not possible | ✅ Optional via env var |
| Code Changes | ❌ Scattered API_URL calls | ✅ Centralized in helper |
| Render Deployment | ❌ Requires env var setup | ✅ Works out of the box |

## Testing

After deployment to Render:

1. ✅ Visit `https://trafficsafe.onrender.com/ui/accidents`
2. ✅ Filters should load (no "API not reachable" error)
3. ✅ Accident list should display (if data exists)
4. ✅ CSV export should work
5. ✅ Import functionality should work

## Files Modified
- `app.py` - Changed API_URL default to empty string
- `ui/accidents_ui.py` - Added `get_api_url()` helper, updated all 9 API calls

## Deployment Instructions

**No environment variable setup needed!** The fix works automatically on Render because:
1. Both UI and API routes are served by the same Flask app
2. The UI now makes same-origin requests to its own API endpoints
3. This is the recommended approach for monolithic applications

Simply push the changes to GitHub and Render will auto-deploy.

## Optional: Using a Separate API Server

If you ever move the API to a separate server, set this environment variable:
```
API_URL=https://api.yourdomain.com
```

The code will automatically use it without any other changes.
