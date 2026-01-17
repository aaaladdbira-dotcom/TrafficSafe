# Fix: "No Accidents Found" on Production

## Problem
When visiting `https://trafficsafe.onrender.com/ui/accidents`, the page displays:
```
No accidents found
There are no accident records matching your filters. Try adjusting your search criteria or import some data.
```

## Root Cause
The UI layer (`ui/accidents_ui.py`) had **hardcoded localhost URLs** pointing to `http://127.0.0.1:5001` for all API calls:
- `/api/v1/accidents`
- `/api/v1/accidents/filters`
- `/api/v1/accidents/export`
- `/upload/import/batches`
- `/upload/import`

On a production deployment (Render), these localhost URLs cannot be reached, causing all API calls to fail silently and returning empty accident lists.

## Solution

### 1. Updated `ui/accidents_ui.py`
Replaced all 5 hardcoded localhost URLs with dynamic API_URL configuration:

**Before:**
```python
resp = requests.get(
    "http://127.0.0.1:5001/api/v1/accidents",
    headers=headers,
    params=params,
    timeout=5
)
```

**After:**
```python
api_url = current_app.config.get('API_URL', 'http://localhost:5001')
resp = requests.get(
    f"{api_url}/api/v1/accidents",
    headers=headers,
    params=params,
    timeout=5
)
```

All 5 endpoints now use the configurable `API_URL`:
- Line 104: `accidents()` filter endpoint
- Line 131: `accidents()` main list endpoint  
- Line 274: `accidents_data()` proxy endpoint
- Line 320: `accidents_filters_proxy()` endpoint
- Line 353: `accidents_export_proxy()` endpoint
- Line 381: `accidents_batches_proxy()` endpoint
- Line 407: `clear_imports()` endpoint

### 2. Updated `app.py`
Added API_URL configuration at line 120:

```python
# API_URL for UI to communicate with API layer (uses same origin by default)
app.config["API_URL"] = os.environ.get("API_URL", "http://localhost:5001")
```

This allows the API URL to be configured via environment variables while maintaining backward compatibility with local development.

## Deployment Instructions

On Render, set the environment variable:
```
API_URL=https://trafficsafe.onrender.com
```

Or if the API is served on a different domain/port:
```
API_URL=https://api.yourdomain.com
```

For local development, no action needed (defaults to `http://localhost:5001`).

## Testing

After deploying these changes:

1. Visit `https://trafficsafe.onrender.com/ui/accidents`
2. The accidents list should now load successfully (assuming there is data in the database)
3. Filters should work properly
4. CSV export and import should function correctly

## Files Modified
- `ui/accidents_ui.py` - Fixed 7 API URL calls
- `app.py` - Added API_URL configuration

## Related Files
Other UI modules use the correct pattern:
- `ui/users_ui.py` - Already uses `current_app.config.get('API_URL', ...)`
- `ui/report_ui.py` - Already uses `current_app.config.get('API_URL', ...)`

This fix standardizes the accidents UI to match the same pattern.
