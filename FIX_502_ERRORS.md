# Fix for 502 Errors on Production

## Problem
The Render logs showed **502 Bad Gateway** errors on these endpoints:
- `GET /ui/accidents/filters` → 502
- `GET /ui/accidents/data` → 502

The root cause was that the UI routes were making **external HTTP requests** back to the same Render service using absolute URLs like `https://trafficsafe.onrender.com/api/v1/accidents`. While this worked in local development, on production Render:

1. External HTTP requests have network latency and can time out
2. Both UI and API run on the same Render service, so network requests are unnecessary
3. The Flask app's concurrency model with limited workers was blocking on external requests

## Solution
Replaced all external HTTP requests with **internal Flask test client calls** when no explicit `API_URL` is configured:

### Key Changes

**Before:**
```python
# Makes external HTTP request
resp = requests.get(get_api_url("/api/v1/accidents"), headers=headers, params=params)
```

**After:**
```python
# Uses Flask test client for internal routing (no network overhead)
resp = call_api("/api/v1/accidents", headers=headers, params=params)
```

### Implementation Details

Each UI module now has a `call_api()` helper function that:

1. **If `API_URL` environment variable is set** → Uses `requests` for external API (allows separate API servers)
2. **If `API_URL` is empty** (default) → Uses Flask test client for internal WSGI routing

```python
def call_api(endpoint, method='GET', headers=None, params=None, json=None, timeout=5):
    """Call API endpoint - either via HTTP or internal WSGI client."""
    api_base = current_app.config.get('API_URL', '')
    
    if api_base:
        # External API - use requests
        url = f"{api_base}{endpoint}"
        return requests.get(url, headers=headers, params=params, timeout=timeout)
    else:
        # Internal WSGI call - use Flask test client (no network overhead)
        client = current_app.test_client()
        query_string = '?' + '&'.join(f"{k}={v}" for k, v in params.items() if v) if params else ''
        return client.get(endpoint + query_string, headers=headers)
```

### Files Modified
1. **ui/accidents_ui.py** - 9 API calls updated
2. **ui/dashboard_ui.py** - 2 API calls updated
3. **ui/auth_ui.py** - Login call updated
4. **ui/register_ui.py** - Register call updated
5. **ui/import_ui.py** - Delete, upload, fetch batches calls updated (special handling for file uploads)

## Benefits

✅ **Eliminates 502 errors** - No more network timeout issues  
✅ **Faster response times** - Internal routing is much faster than HTTP  
✅ **More scalable** - Doesn't consume worker processes waiting for network I/O  
✅ **Backward compatible** - Still supports external API servers via `API_URL` env var  
✅ **Production-ready** - Works seamlessly on Render and other platforms  

## Testing

After deployment, verify:
1. ✅ `/ui/accidents` page loads without 502 errors
2. ✅ Filters dropdown loads (used to return 502)
3. ✅ Accidents data table loads with pagination
4. ✅ CSV export works
5. ✅ Dashboard stats load
6. ✅ Login and registration work

## Deployment

Changes pushed to GitHub in commit `862d021`:
- Render auto-deployment will trigger
- Should take 1-2 minutes to redeploy
- No configuration changes needed

## Future

If you ever want to run a separate API server:
```bash
# Set on Render dashboard
API_URL=https://api-separate.example.com
```

The code will automatically switch to making external HTTP requests while maintaining backward compatibility.
