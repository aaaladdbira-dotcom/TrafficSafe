
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, jsonify
import requests
from .utils import login_required

accidents_ui = Blueprint("accidents_ui", __name__)


def get_api_url(endpoint):
    """Build API URL - either external or internal WSGI call.
    
    If API_URL is explicitly configured in env, use it for external API.
    Otherwise, use Flask test client to make internal WSGI calls (no network overhead).
    """
    api_base = current_app.config.get('API_URL', '')
    
    if api_base:
        # Explicitly configured external API URL
        return f"{api_base}{endpoint}"
    else:
        # Internal WSGI call - return None to signal caller to use test client
        return None


def call_api(endpoint, method='GET', headers=None, params=None, json=None, timeout=5):
    """Call API endpoint - either via HTTP or internal WSGI client.
    
    If get_api_url returns a URL, use requests.
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
            # Return a fake response-like object for exception handling
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
            # Return a fake response-like object for exception handling
            class FakeResponse:
                def __init__(self, error):
                    self.status_code = 502
                    self.text = str(error)
                def json(self):
                    raise ValueError("No JSON")
            return FakeResponse(e)

# Edit accident route (government only)
@accidents_ui.route('/accidents/<int:accident_id>/edit', methods=['GET'])
@login_required
def edit_accident(accident_id):
    # Only allow government users
    if session.get('role') != 'government':
        flash('Access denied.', 'danger')
        return redirect(url_for('accidents_ui.accidents'))
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    resp = call_api("/api/v1/accidents", headers=headers, params={"id": accident_id})
    accident = None
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict) and data.get("items"):
            for a in data["items"]:
                if a["id"] == accident_id:
                    accident = a
                    break
        elif isinstance(data, list):
            for a in data:
                if a["id"] == accident_id:
                    accident = a
                    break
    if not accident:
        flash("Accident not found.", "danger")
        return redirect(url_for('accidents_ui.accidents'))
    return render_template("edit_accident.html", accident=accident)

# Debug endpoint to list all UI routes
@accidents_ui.route('/_routes', methods=['GET'])
@login_required
def debug_routes():
    out = []
    try:
        for rule in current_app.url_map.iter_rules():
            if str(rule.rule).startswith('/ui'):
                out.append({
                    'rule': rule.rule,
                    'endpoint': rule.endpoint,
                    'methods': sorted([m for m in rule.methods if m not in ('HEAD','OPTIONS')])
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'routes': out}), 200

@accidents_ui.route('/accidents/<int:accident_id>')
@login_required
def accident_detail(accident_id):
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    resp = call_api("/api/v1/accidents", headers=headers, params={"id": accident_id})
    accident = None
    if resp.status_code == 200:
        data = resp.json()
        # If paginated, find the accident by id
        if isinstance(data, dict) and data.get("items"):
            for a in data["items"]:
                if a["id"] == accident_id:
                    accident = a
                    break
        elif isinstance(data, list):
            for a in data:
                if a["id"] == accident_id:
                    accident = a
                    break
    if not accident:
        flash("Accident not found.", "danger")
        return render_template("accident_detail.html", accident=None)
    # Try to get linked report id if present
    report_id = None
    if "report" in accident and accident["report"] and isinstance(accident["report"], dict):
        report_id = accident["report"].get("id")
    accident["report_id"] = report_id
    role = session.get('role')
    return render_template("accident_detail.html", accident=accident, role=role)
@accidents_ui.route("/accidents")
@login_required
def accidents():
    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }
    # Forward UI query params to the API so filtering works
    params = {}
    for k in ("location", "cause", "severity", "delegation", "start_date", "end_date"):
        v = request.args.get(k)
        if v:
            params[k] = v

    # Pagination params
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "25")
    params["page"] = page
    params["per_page"] = per_page

    # Get filter option lists from the API (full distinct values)
    try:
        resp_filters = call_api("/api/v1/accidents/filters", headers=headers, timeout=5)
        if resp_filters.status_code == 200:
            fdata = resp_filters.json()
            # API returns data wrapped in "data" key
            filter_data = fdata.get("data", {})
            locations = filter_data.get("locations", [])
            causes = filter_data.get("causes", [])
            severities = filter_data.get("severities", [])
            delegations = filter_data.get("delegations", [])
        else:
            locations = []
            causes = []
            severities = []
            delegations = []
    except Exception:
        locations = []
        causes = []
        severities = []
        delegations = []

    try:
        resp = call_api("/api/v1/accidents", headers=headers, params=params, timeout=5)
    except Exception as e:
        flash("API not reachable", "danger")
        return render_template("accidents_list.html", accidents=[],
                               selected_location=request.args.get("location", ""),
                               selected_cause=request.args.get("cause", ""),
                               selected_severity=request.args.get("severity", ""),
                               selected_delegation=request.args.get("delegation", ""),
                               start_date=request.args.get("start_date", ""),
                               end_date=request.args.get("end_date", ""),
                               locations=locations, causes=causes, severities=severities, delegations=delegations,
                               page=1, per_page=25, total=0,
                               pages=[1], last_page=1, highlight_ids=[])

    if resp.status_code != 200:
        try:
            msg = resp.json().get("message", resp.text)
        except Exception:
            msg = resp.text
        flash(f"Failed to load accidents: {msg}", "warning")
        accidents = []
        total = 0
        page = 1
        per_page = 25
    else:
        rj = resp.json()
        # support paginated response with 'data' or 'items' or legacy list
        if isinstance(rj, dict):
            # New API format: {data: [...], pagination: {total, page, per_page}}
            if rj.get("data") is not None:
                accidents = rj.get("data", [])
                pagination = rj.get("pagination", {})
                total = pagination.get("total", 0)
                try:
                    page = int(pagination.get("page", page))
                    per_page = int(pagination.get("per_page", per_page))
                except Exception:
                    page = int(page)
                    per_page = int(per_page)
            # Legacy format: {items: [...], total, page, per_page}
            elif rj.get("items") is not None:
                accidents = rj.get("items", [])
                total = rj.get("total", 0)
                try:
                    page = int(rj.get("page", page))
                    per_page = int(rj.get("per_page", per_page))
                except Exception:
                    page = int(page)
                    per_page = int(per_page)
            else:
                accidents = []
                total = 0
        else:
            accidents = rj if isinstance(rj, list) else []
            total = len(accidents)

    # highlight IDs if provided in querystring
    highlight_ids = request.args.get('highlight_ids', '')
    highlight_set = [int(x) for x in highlight_ids.split(',') if x.strip().isdigit()] if highlight_ids else []
    # Compute condensed pagination pages list server-side so templates stay simple.
    try:
        cur = int(page)
        pp = int(per_page)
    except Exception:
        cur = 1
        pp = 25

    last_page = max(1, (int(total) // pp) + (1 if int(total) % pp else 0)) if total is not None else 1

    def build_pages(current, last, window=2):
        pages = []
        if last <= 1:
            return [1]
        pages.append(1)
        left = max(2, current - window)
        right = min(last - 1, current + window)
        if left > 2:
            pages.append('...')
        elif left == 2:
            pages.append(2)
        for p in range(left, right + 1):
            if p > 1 and p < last:
                if p not in pages:
                    pages.append(p)
        if right < last - 1:
            pages.append('...')
        elif right == last - 1:
            if last - 1 not in pages:
                pages.append(last - 1)
        if last > 1:
            pages.append(last)
        # ensure unique and ordered
        out = []
        for p in pages:
            if p not in out:
                out.append(p)
        return out

    pages = build_pages(cur, last_page, window=2)

    return render_template(
        "accidents_list.html",
        accidents=accidents,
        selected_location=request.args.get("location", ""),
        selected_cause=request.args.get("cause", ""),
        selected_severity=request.args.get("severity", ""),
        selected_delegation=request.args.get("delegation", ""),
        start_date=request.args.get("start_date", ""),
        end_date=request.args.get("end_date", ""),
        locations=locations,
        causes=causes,
        severities=severities,
        delegations=delegations,
        page=cur,
        per_page=pp,
        total=total,
        highlight_ids=highlight_set,
        pages=pages,
        last_page=last_page,
    )


@accidents_ui.route('/accidents/data')
@login_required
def accidents_data():
    """Proxy endpoint for AJAX: forwards query params to /api/accidents and returns JSON.

    This avoids exposing the JWT to the browser by attaching the server-side session token.
    """
    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }
    params = {}
    for k in ("location", "delegation", "cause", "severity", "start_date", "end_date", "page", "per_page"):
        v = request.args.get(k)
        if v:
            params[k] = v

    try:
        resp = call_api("/api/v1/accidents", headers=headers, params=params, timeout=5)
    except Exception:
        return {"items": [], "total": 0, "page": 1, "per_page": int(request.args.get('per_page', 25))}, 502

    # Try to return JSON from the API. If the API returned non-JSON (e.g., an
    # HTML error page with a SQLAlchemy traceback), forward the text so the UI
    # can surface the underlying error message instead of raising a 500 here.
    try:
        data = resp.json()
        # API uses paginated_response which wraps data in {"data": [...], "pagination": {...}}
        # Unwrap it to match the format expected by the frontend
        if isinstance(data, dict) and 'data' in data and 'pagination' in data:
            return {
                "items": data['data'],
                "total": data['pagination']['total'],
                "page": data['pagination']['page'],
                "per_page": data['pagination']['per_page']
            }, resp.status_code
        return data, resp.status_code
    except Exception:
        # Forward plain text body with the API status code so the client can
        # show a helpful error message.
        text = None
        try:
            text = resp.text
        except Exception:
            text = 'Unexpected non-JSON response from API'
        return {"error": text, "items": [], "total": 0, "page": 1, "per_page": int(request.args.get('per_page', 25))}, resp.status_code


@accidents_ui.route('/accidents/filters')
@login_required
def accidents_filters_proxy():
    """Proxy endpoint for filter option lists.
    Forwards to /api/accidents/filters and returns JSON.
    """
    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }
    try:
        resp = call_api("/api/v1/accidents/filters", headers=headers, timeout=5)
    except Exception:
        return {"locations": [], "causes": [], "severities": [], "delegations": []}, 502

    try:
        data = resp.json()
        # API wraps data in success_response, unwrap it for the frontend
        if isinstance(data, dict) and 'data' in data:
            return data['data'], resp.status_code
        return data, resp.status_code
    except Exception:
        return {"locations": [], "causes": [], "severities": [], "delegations": []}, 500


@accidents_ui.route('/accidents/export')
@login_required
def accidents_export_proxy():
    """Proxy to download CSV export from API while using server session JWT."""
    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }
    params = {}
    for k in ("location", "cause", "severity", "start_date", "end_date"):
        v = request.args.get(k)
        if v:
            params[k] = v

    try:
        resp = call_api("/api/v1/accidents/export", headers=headers, params=params, timeout=10)
    except Exception:
        from flask import abort
        abort(502, "Export failed: API not reachable")

    from flask import Response
    # pass through CSV bytes
    response = Response(resp.content, status=resp.status_code, mimetype=resp.headers.get('Content-Type', 'text/csv'))
    disposition = resp.headers.get('Content-Disposition')
    if disposition:
        response.headers['Content-Disposition'] = disposition
    return response


@accidents_ui.route('/accidents/batches')
@login_required
def accidents_batches_proxy():
    """Proxy to return import batches for UI pages (government only)."""
    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }
    try:
        resp = call_api("/upload/import/batches", headers=headers, timeout=5)
    except Exception:
        return {"batches": []}, 502

    try:
        return resp.json(), resp.status_code
    except Exception:
        return {"batches": []}, 500


@accidents_ui.route('/accidents/clear_imports', methods=['POST'])
@login_required
def clear_imports():
    """Clear all imported records (proxy) by calling the import delete endpoint without batch_id.

    This mirrors the behavior in import_ui but keeps the user on the accidents UI flow.
    """
    headers = {
        "Authorization": f"Bearer {session.get('access_token')}"
    }
    try:
        resp = requests.delete(
            get_api_url("/upload/import"),
            headers=headers,
            timeout=10,
        )
    except Exception:
        flash("API not reachable", "danger")
        # Return a minimal but compatible context so the template has pagination values
        return render_template("accidents_list.html",
                               accidents=[],
                               selected_location='', selected_cause='', selected_severity='',
                               start_date='', end_date='',
                               locations=[], causes=[], severities=[],
                               page=1, per_page=25, total=0,
                               pages=[1], last_page=1, highlight_ids=[])

    if resp.status_code != 200:
        try:
            data = resp.json()
            msg = data.get("message") or data.get("msg") or resp.text
        except Exception:
            msg = resp.text

        if resp.status_code == 401 and ("expired" in (msg or "").lower() or "token" in (msg or "").lower()):
            session.clear()
            flash("Session expired — please log in again", "warning")
            from flask import redirect, url_for
            return redirect(url_for("auth_ui.login"))

        flash(msg or "Delete failed", "danger")
        from flask import redirect, url_for
        return redirect(url_for("accidents_ui.accidents"))

    # success
    try:
        data = resp.json()
        deleted = data.get('deleted', 0)
    except Exception:
        deleted = 0
    flash(f"Deleted: {deleted} records", "success")
    from flask import redirect, url_for
    return redirect(url_for("accidents_ui.accidents"))


