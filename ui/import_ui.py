from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
import requests
from .utils import login_required, role_required

import_ui = Blueprint("import_ui", __name__)


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
            elif method.upper() == 'DELETE':
                return requests.delete(url, headers=headers, params=params, json=json, timeout=timeout)
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
            elif method.upper() == 'DELETE':
                resp = client.delete(endpoint + query_string, headers=headers, json=json)
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


@import_ui.route("/import", methods=["GET", "POST"])
@login_required
@role_required("government")
def import_csv():
    if request.method == "POST":
        # Deletion action (only for government role) comes as a form field 'action=delete'
        if request.form.get("action") == "delete":
            headers = {"Authorization": f"Bearer {session['access_token']}"}
            batch_id = request.form.get('batch_id')
            try:
                resp = call_api("/upload/import", method='DELETE', headers=headers, params={'batch_id': batch_id} if batch_id else None, timeout=10)
            except Exception:
                flash("API not reachable", "danger")
                return redirect(url_for("import_ui.import_csv"))

            if resp.status_code != 200:
                # Handle expired token specially
                try:
                    data = resp.json()
                    msg = data.get("message") or data.get("msg") or resp.text
                except Exception:
                    msg = resp.text

                if resp.status_code == 401 and ("expired" in (msg or "").lower() or "token" in (msg or "").lower()):
                    # Clear server session and ask user to re-login
                    session.clear()
                    flash("Session expired — please log in again", "warning")
                    return redirect(url_for("auth_ui.login"))

                flash(msg or "Delete failed", "danger")
                return redirect(url_for("import_ui.import_csv"))

            data = resp.json()
            flash(f"Deleted: {data.get('deleted', 0)} records", "success")
            return redirect(url_for("accidents_ui.accidents"))

        # Otherwise handle upload
        file = request.files.get("file")

        if not file:
            flash("No file selected", "danger")
            return redirect(url_for("import_ui.import_csv"))

        headers = {
            "Authorization": f"Bearer {session['access_token']}"
        }

        try:
            # For file uploads, we need to handle external API differently
            api_base = current_app.config.get('API_URL', '')
            if api_base:
                # External API - use requests which handles multipart/form-data
                resp = requests.post(
                    f"{api_base}/upload/import",
                    files={"file": (file.filename, file.stream, file.content_type)},
                    headers=headers,
                    timeout=10
                )
            else:
                # Internal - for Flask test client, we need to read the file content
                file_content = file.read()
                file.seek(0)  # Reset for potential re-reads
                resp = current_app.test_client().post(
                    "/upload/import",
                    data={'file': (file.stream, file.filename)},
                    headers=headers
                )
        except Exception:
            flash("API not reachable", "danger")
            return redirect(url_for("import_ui.import_csv"))

        if resp.status_code != 200:
            # show raw response text when possible for easier debugging (e.g., missing/invalid JWT)
            try:
                data = resp.json()
                msg = data.get("message") or data.get("msg") or resp.text
            except Exception:
                msg = resp.text

            if resp.status_code == 401 and ("expired" in (msg or "").lower() or "token" in (msg or "").lower()):
                session.clear()
                flash("Session expired — please log in again", "warning")
                return redirect(url_for("auth_ui.login"))

            flash(msg or "Import failed", "danger")
            return redirect(url_for("import_ui.import_csv"))

        data = resp.json()
        # Surface counts and any row-level errors returned by the import API so
        # the user can diagnose why rows were skipped (invalid dates, severity, etc.)
        imported = data.get('imported', 0)
        skipped = data.get('skipped', 0)
        flash(f"Imported: {imported}, Skipped: {skipped}", "success")
        errors = data.get('errors', []) or []
        if errors:
            # show up to first 10 errors to avoid flooding the UI
            msgs = []
            for e in errors[:10]:
                # each error is expected like {'row': N, 'reason': '...'}
                try:
                    row = e.get('row')
                    reason = e.get('reason')
                    msgs.append(f"Row {row}: {reason}")
                except Exception:
                    msgs.append(str(e))
            flash("Import errors (first 10):\n" + "\n".join(msgs), "warning")

        # If import returned created IDs, pass them to the accidents page so
        # newly created rows can be highlighted.
        created = data.get('created_ids', [])
        if created:
            ids_param = ",".join(str(i) for i in created)
            # Add a cache-busting timestamp to the redirect so the accidents
            # page reloads fresh data immediately after an import. Some dev
            # environments or proxies may cache GETs; including a unique
            # query param prevents stale results.
            import time
            ts = int(time.time())
            return redirect(url_for("accidents_ui.accidents") + f"?highlight_ids={ids_param}&_ts={ts}")

        return redirect(url_for("accidents_ui.accidents"))

    # GET: fetch available import batches to show history
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    batches = []
    try:
        resp = call_api("/upload/import/batches", headers=headers, timeout=5)
        if resp.status_code == 200:
            batches = resp.json().get('batches', [])
    except Exception:
        batches = []

    return render_template("import_csv.html", batches=batches)
