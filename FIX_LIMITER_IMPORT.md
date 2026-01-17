# Fix Applied: Limiter Import Error

## Problem
The application failed to start with the following error:
```
ImportError: cannot import name 'limiter' from 'extensions'
```

## Root Cause
The `contact.py` resource module tried to import `limiter` from `extensions.py`, but the limiter was only initialized in `app.py` at the module level and was not exported from extensions.

## Solution Applied

### 1. Updated `extensions.py`
Added limiter initialization to the extensions module:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://"
)
```

### 2. Updated `app.py`
Changed the import to use limiter from extensions:
- **Before**: `from extensions import db, jwt, migrate`
- **After**: `from extensions import db, jwt, migrate, limiter`

Removed duplicate limiter initialization from app.py:
```python
# Removed these lines (now in extensions.py)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(...)
```

## Result
✅ Application now starts without errors
✅ All new pages load successfully:
- `/about`
- `/faq`
- `/privacy`
- `/terms`
- `/contact`

✅ Server running on http://127.0.0.1:5001

## Files Modified
1. `extensions.py` - Added limiter export
2. `app.py` - Updated imports and removed duplicate limiter initialization

## Testing Confirmation
All pages verified to load successfully in the browser.
