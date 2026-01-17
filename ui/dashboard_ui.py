from flask import Blueprint, render_template, session, current_app, request
import requests
from .utils import login_required
import hashlib
from datetime import datetime, timedelta

dashboard_ui = Blueprint("dashboard_ui", __name__)


def call_api(endpoint, method='GET', headers=None, params=None, json=None, timeout=5):
    """Call API endpoint - either via HTTP or internal WSGI client.
    
    If API_URL is configured, use requests for external API.
    Otherwise, use Flask test client for internal routing.
    """
    api_base = current_app.config.get('API_URL', '')
    
    if api_base:
        # External API - use requests
        url = f"{api_base}{endpoint}"
        try:
            if method.upper() == 'GET':
                return requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                return requests.post(url, headers=headers, params=params, json=json, timeout=timeout)
            else:
                return requests.request(method, url, headers=headers, params=params, json=json, timeout=timeout)
        except Exception as e:
            class FakeResponse:
                def __init__(self, error):
                    self.status_code = 502
                    self.text = str(error)
                def json(self):
                    raise ValueError("No JSON")
            return FakeResponse(e)
    else:
        # Internal WSGI call - use Flask test client
        try:
            client = current_app.test_client()
            query_string = ''
            if params:
                query_string = '?' + '&'.join(f"{k}={v}" for k, v in params.items() if v)
            
            if method.upper() == 'GET':
                resp = client.get(endpoint + query_string, headers=headers)
            elif method.upper() == 'POST':
                resp = client.post(endpoint + query_string, headers=headers, json=json)
            else:
                resp = client.open(endpoint + query_string, method=method, headers=headers, json=json)
            
            return resp
        except Exception as e:
            class FakeResponse:
                def __init__(self, error):
                    self.status_code = 502
                    self.text = str(error)
                def json(self):
                    raise ValueError("No JSON")
            return FakeResponse(e)


@dashboard_ui.route("/dashboard")
@login_required
def dashboard():
    # Prepare default values
    accidents_count = None
    last_import = None
    imports_today = None
    skipped_rows_last = None

    headers = {
        "Authorization": f"Bearer {session.get('access_token')}"
    }

    # Get total accidents (use API pagination total if available)
    try:
        resp = call_api("/api/v1/accidents", headers=headers, params={"page": 1, "per_page": 1}, timeout=5)
        if resp.status_code == 200:
            rj = resp.json()
            if isinstance(rj, dict) and rj.get('total') is not None:
                accidents_count = int(rj.get('total', 0))
            elif isinstance(rj, list):
                accidents_count = len(rj)
    except Exception:
        accidents_count = None

    # Get last import batch info and statistics
    try:
        resp = call_api("/upload/import/batches", headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Accept either {'batches': [...]} or a list
            batches = []
            if isinstance(data, dict) and data.get('batches') is not None:
                batches = data.get('batches')
            elif isinstance(data, list):
                batches = data
            if batches:
                # compute statistics: last import timestamp, skipped rows for last import, imports in last 24h
                now = datetime.utcnow()
                imports_last_24h = 0
                skipped_last = None
                # iterate batches (expecting dicts with created_at/imported_count/skipped_count)
                for b in batches:
                    if not isinstance(b, dict):
                        continue
                    ca = b.get('created_at') or b.get('created') or b.get('timestamp')
                    try:
                        if ca:
                            dt = datetime.fromisoformat(ca)
                        else:
                            dt = None
                    except Exception:
                        dt = None

                    # imported_count
                    try:
                        ic = int(b.get('imported_count') or b.get('imported') or 0)
                    except Exception:
                        ic = 0

                    # skipped_count
                    try:
                        sc = int(b.get('skipped_count') or b.get('skipped') or 0)
                    except Exception:
                        sc = 0

                    # sum imports in last 24 hours if timestamp available
                    if dt is not None:
                        if (now - dt) <= timedelta(days=1):
                            imports_last_24h += ic
                    # if this is the newest batch (first in list) capture last_import and skipped
                    if b is batches[0]:
                        if dt:
                            try:
                                last_import = dt.strftime('%Y-%m-%d %H:%M')
                            except Exception:
                                last_import = str(ca)
                        else:
                            last_import = ca or None
                        skipped_last = sc
                imports_today = imports_last_24h
                skipped_rows_last = skipped_last
    except Exception:
        last_import = None
        imports_today = None
        skipped_rows_last = None

    # gravatar
    email = session.get('email', '') or ''
    e = email.strip().lower().encode('utf-8')
    gravatar_hash = hashlib.md5(e).hexdigest() if e else ''
    gravatar_url = f"https://www.gravatar.com/avatar/{gravatar_hash}?d=identicon&s=96" if gravatar_hash else ''

    # Query user from DB for details
    from models.user import User
    user = User.query.filter_by(email=email).first() if email else None

    return render_template(
        "dashboard.html",
        role=session.get("role"),
        email=session.get("email"),
        gravatar_url=gravatar_url,
        status='Active',
        accidents_count=accidents_count,
        last_import=last_import,
        imports_today=imports_today,
        skipped_rows_last=skipped_rows_last,
        user=user,
    )
