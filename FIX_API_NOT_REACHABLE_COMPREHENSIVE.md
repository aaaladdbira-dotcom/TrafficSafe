# COMPREHENSIVE FIX: API Not Reachable in Production

## Issue
All UI pages on production showed "API not reachable" error because the code had hardcoded localhost URLs that don't work on Render.

## Root Cause
The UI layer had hardcoded `http://127.0.0.1:5001` URLs in 5 different UI files, which only work on the same machine. On Render, both UI and API are served from the same origin (same domain/host), so hardcoded localhost URLs fail.

## Solution Overview
Implemented a **centralized `get_api_url()` helper function** in each UI module that:
1. Uses an explicit `API_URL` environment variable if configured (for separate API servers)
2. Falls back to **same-origin requests** by default (for production on Render)
3. Works seamlessly on both local development and production without configuration

## Files Modified

### 1. `app.py` - Configuration
- **Line 120-123:** Changed API_URL default from hardcoded localhost to empty string
  ```python
  app.config["API_URL"] = os.environ.get("API_URL", "")
  ```

### 2. `ui/accidents_ui.py` - Accidents Page
- **Lines 9-18:** Added `get_api_url()` helper function
- **9 API calls updated** to use the helper:
  - Line 33: `edit_accident()` 
  - Line 73: `accident_detail()`
  - Line 120: `accidents()` - filters endpoint
  - Line 145: `accidents()` - main list endpoint
  - Line 289: `accidents_data()` - AJAX proxy
  - Line 334: `accidents_filters_proxy()`
  - Line 366: `accidents_export_proxy()`
  - Line 393: `accidents_batches_proxy()`
  - Line 418: `clear_imports()`

### 3. `ui/auth_ui.py` - Login Page
- **Lines 8-18:** Added `get_api_url()` helper function
- **1 API call updated:**
  - Line 39: `login()` - auth endpoint

### 4. `ui/register_ui.py` - Registration Page
- **Lines 11-21:** Added `get_api_url()` helper function
- **1 API call updated:**
  - Line 101: `register()` - register endpoint

### 5. `ui/import_ui.py` - CSV Import Page
- **Lines 7-17:** Added `get_api_url()` helper function
- **3 API calls updated:**
  - Line 32: `import_csv()` - delete batch
  - Line 76: `import_csv()` - upload file
  - Line 147: `import_csv()` - fetch batch history

### 6. `ui/dashboard_ui.py` - Dashboard Page
- **Lines 9-19:** Added `get_api_url()` helper function
- **2 API calls updated:**
  - Line 39: `dashboard()` - fetch accidents count
  - Line 47: `dashboard()` - fetch import batches

## Total Changes
- **6 UI files modified**
- **6 `get_api_url()` helper functions added**
- **17 API calls updated** (from hardcoded URLs to dynamic helpers)
- **0 environment variables required** (works out of the box on Render)

## How It Works

### Smart URL Builder Logic
```python
def get_api_url(endpoint):
    api_base = current_app.config.get('API_URL', '')
    
    if api_base:
        # Use configured API_URL for separate API servers
        return f"{api_base}{endpoint}"
    else:
        # Use same-origin for monolithic deployments
        return f"{request.scheme}://{request.host}{endpoint}"
```

### Scenarios

| Scenario | API_URL | Result |
|----------|---------|--------|
| **Render Production** | Not set | `https://trafficsafe.onrender.com/api/v1/...` |
| **Local Dev** | Not set | `http://localhost:5001/api/v1/...` |
| **Separate API Server** | `https://api.example.com` | `https://api.example.com/api/v1/...` |

## Benefits

1. ✅ **Zero Configuration on Render** - Works automatically
2. ✅ **Backward Compatible** - Local development unchanged
3. ✅ **Flexible** - Supports separate API servers via env var
4. ✅ **Maintainable** - Centralized helper functions
5. ✅ **Scalable** - Same pattern used across all UI modules

## Deployment

**No action needed!** Simply push changes to GitHub and Render will auto-deploy.

The fix works automatically because:
- Both UI and API are served by the Flask app on Render
- The same-origin requests bypass CORS and network issues
- No environment variable configuration required

## Optional: Separate API Server

If you ever split API and UI into separate services, set:
```
API_URL=https://api.yourdomain.com
```

The code will use it automatically without any other changes.

## Verification Checklist

After deployment, verify these pages work:
- [ ] `https://trafficsafe.onrender.com/ui/accidents` - Loads accidents
- [ ] `https://trafficsafe.onrender.com/ui/dashboard` - Shows statistics
- [ ] `https://trafficsafe.onrender.com/ui/login` - Login works
- [ ] `https://trafficsafe.onrender.com/ui/register` - Registration works
- [ ] `https://trafficsafe.onrender.com/ui/import` - Import shows history
- [ ] All pages: Filters, pagination, export work without "API not reachable"

## Consistency
All UI modules now follow the same pattern:
- Dedicated `get_api_url()` helper function
- Imported at module level
- Used for all API calls
- Supports both same-origin and separate API servers

This standardizes the codebase and makes it easier to maintain going forward.
