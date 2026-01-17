from flask import Blueprint, render_template, session, redirect, url_for, flash, current_app, request
import requests

gov_reports_ui = Blueprint('gov_reports_ui', __name__)

from flask import Blueprint, render_template, session, redirect, url_for, flash, current_app, request
import requests

print('gov_reports_ui.py is being imported')
gov_reports_ui = Blueprint('gov_reports_ui', __name__)


@gov_reports_ui.route('/reports/debug')
def reports_debug():
    return 'gov_reports_ui blueprint is loaded', 200

@gov_reports_ui.route('/reports')
def reports_list():
    if 'role' not in session or session['role'] != 'government':
        flash('Access denied. Government only.', 'danger')
        return redirect(url_for('dashboard_ui.dashboard'))
    jwt_token = session.get('access_token')
    api_url = current_app.config.get('API_URL', 'http://localhost:5001')
    headers = {'Authorization': f'Bearer {jwt_token}'} if jwt_token else {}
    try:
        resp = requests.get(f'{api_url}/reports', headers=headers)
        reports = resp.json() if resp.status_code == 200 else []
    except Exception:
        reports = []
    return render_template('gov_reports.html', reports=reports)

@gov_reports_ui.route('/reports/<int:report_id>', methods=['GET', 'POST'])
def report_detail(report_id):
    if 'role' not in session or session['role'] != 'government':
        flash('Access denied. Government only.', 'danger')
        return redirect(url_for('dashboard_ui.dashboard'))
    jwt_token = session.get('access_token')
    api_url = current_app.config.get('API_URL', 'http://localhost:5001')
    headers = {'Authorization': f'Bearer {jwt_token}'} if jwt_token else {}
    # Handle confirm/reject
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'confirm':
            resp = requests.post(f'{api_url}/reports/{report_id}/confirm', headers=headers)
            if resp.status_code == 200:
                flash('Report confirmed and accident created.', 'success')
            else:
                # Handle non-JSON or empty error response
                if resp.content and resp.headers.get('Content-Type', '').startswith('application/json'):
                    try:
                        msg = resp.json().get('description', 'Failed to confirm.')
                    except Exception:
                        msg = resp.text or 'Failed to confirm.'
                else:
                    msg = resp.text or 'Failed to confirm.'
                flash(msg, 'danger')
        elif action == 'reject':
            reason = request.form.get('reason')
            resp = requests.post(f'{api_url}/reports/{report_id}/reject', json={'reason': reason}, headers=headers)
            if resp.status_code == 200:
                flash('Report rejected.', 'warning')
            else:
                try:
                    msg = resp.json().get('description', 'Failed to reject.')
                except Exception:
                    msg = resp.text or 'Failed to reject.'
                flash(msg, 'danger')
        return redirect(url_for('gov_reports_ui.reports_list'))
    # GET: show report detail
    try:
        resp = requests.get(f'{api_url}/reports/{report_id}', headers=headers)
        report = resp.json() if resp.status_code == 200 else None
    except Exception:
        report = None
    return render_template('gov_report_detail.html', report=report)
