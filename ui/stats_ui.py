from flask import Blueprint, render_template, session, current_app, Response
from .utils import login_required

stats_ui = Blueprint("stats_ui", __name__)


@stats_ui.route("/stats")
@login_required
def stats():
    return render_template("statistics.html")


@stats_ui.route('/export/statistics/<format_type>')
@login_required
def statistics_export_proxy(format_type):
    """Proxy statistics export through the UI so the browser doesn't need the JWT.

    Hits `/api/export/statistics/<format_type>` with the server-side JWT and
    returns the binary file and Content-Disposition header to the client.
    """
    # Build target API endpoint
    endpoint = f"/api/export/statistics/{format_type}"
    # Use current session token
    token = session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    current_app.logger.debug('[UI EXPORT] session token present: %s', bool(token))

    # Use internal call helper if available, otherwise fall back to requests/test client
    try:
        from .accidents_ui import call_api
        resp = call_api(endpoint, method='GET', headers=headers, timeout=15)
    except Exception:
        # Fallback: try direct requests to API_URL
        api_base = current_app.config.get('API_URL', '')
        if api_base:
            import requests
            url = f"{api_base}{endpoint}"
            resp = requests.get(url, headers=headers, timeout=15)
        else:
            # Internal test client
            client = current_app.test_client()
            resp = client.get(endpoint, headers=headers)

    # Log proxied response status for debugging
    try:
        current_app.logger.debug('[UI EXPORT] proxied resp status: %s', getattr(resp, 'status_code', None))
    except Exception:
        pass

    # Extract body
    body = None
    try:
        if hasattr(resp, 'content'):
            body = resp.content
        elif hasattr(resp, 'data'):
            body = resp.data
        elif hasattr(resp, 'get_data'):
            try:
                body = resp.get_data()
            except Exception:
                body = None
        else:
            txt = getattr(resp, 'text', None)
            if isinstance(txt, str):
                body = txt.encode('utf-8')
    except Exception:
        body = None

    if body is None:
        return Response('Export failed: empty response from API', status=502, mimetype='text/plain')

    hdrs = getattr(resp, 'headers', {}) or {}
    try:
        mimetype = hdrs.get('Content-Type') if hasattr(hdrs, 'get') else None
    except Exception:
        mimetype = None
    if not mimetype:
        mimetype = 'application/octet-stream'

    status_code = getattr(resp, 'status_code', 200)
    response = Response(body, status=status_code, mimetype=mimetype)

    try:
        disposition = hdrs.get('Content-Disposition') if hasattr(hdrs, 'get') else None
        if disposition:
            response.headers['Content-Disposition'] = disposition
    except Exception:
        pass

    return response
