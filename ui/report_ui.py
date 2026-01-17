from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import requests
from ui.accidents_ui import get_api_url
from datetime import datetime

report_ui = Blueprint('report_ui', __name__)

@report_ui.route('/report-accident', methods=['GET', 'POST'])
def report_accident():
    print("[DEBUG UI] Entered report_accident route, method:", request.method)
    # Only non-government users
    if 'role' not in session or session['role'] == 'government':
        flash('Only non-government users can report accidents.', 'danger')
        return redirect(url_for('dashboard_ui.dashboard'))
    if request.method == 'POST':
        date = request.form.get('date')
        location = request.form.get('location')
        delegation = request.form.get('delegation')
        severity = request.form.get('severity')
        phone = request.form.get('phone')
        # Validation
        errors = []
        if not date:
            errors.append('Date is required.')
        if not location:
            errors.append('Location is required.')
        if not delegation:
            errors.append('Delegation is required.')
        if not severity:
            errors.append('Severity is required.')
        import re
        if not phone or not phone.startswith('+216') or len(phone) != 12 or not re.fullmatch(r'\+216\d{8}', phone):
            errors.append('Phone number must start with +216 and be followed by 8 digits (Tunisia format).')
        print(f"[DEBUG UI] Validation errors: {errors}")
        if errors:
            # Show all errors on the form and preserve entered values
            return render_template('report_accident.html', errors=errors, form={
                'date': date,
                'location': location,
                'delegation': delegation,
                'severity': severity,
                'phone': phone
            })
        print("[DEBUG UI] Validation passed, proceeding to API call.")
        # Submit to API
        jwt_token = session.get('access_token')
        headers = {'Authorization': f'Bearer {jwt_token}'} if jwt_token else {}
        # Map UI severity to API severity
        severity_map = {
            'minor': 'Low',
            'moderate': 'Medium',
            'severe': 'High',
            'fatal': 'High',  # If needed, map fatal to High
        }
        api_severity = severity_map.get(severity, 'Low')
        # API expects 'occurred_at' instead of 'date'
        payload = {
            'occurred_at': date,
            'location': location,
            # 'delegation': delegation,  # Remove if not required by API schema
            'severity': api_severity,
            'phone': phone,
            'reported_by': 'citizen',
        }
        api_url = get_api_url('/api/v1/accidents')
        try:
            print(f"[DEBUG UI] Submitting report to API: url={api_url}, payload={payload}, headers={headers}")
            if api_url:
                resp = requests.post(api_url, json=payload, headers=headers)
            else:
                # Internal WSGI call (for local/test)
                client = current_app.test_client()
                resp = client.post('/api/v1/accidents', json=payload, headers=headers)
            print(f"[DEBUG UI] API response: status_code={resp.status_code}, text={resp.text}")
            if resp.status_code == 201:
                flash('Report submitted successfully! Pending government verification.', 'success')
                return redirect(url_for('report_ui.my_reports'))
            else:
                try:
                    msg = resp.json().get('description', 'Failed to submit report.')
                except Exception:
                    msg = 'Failed to submit report.'
                flash(msg, 'danger')
        except Exception as e:
            print(f"[DEBUG UI] Exception during API call: {e}")
            flash('Could not connect to API.', 'danger')
    return render_template('report_accident.html', errors=None, form=None)

@report_ui.route('/my-reports')
def my_reports():
    if 'role' not in session or session['role'] == 'government':
        flash('Only non-government users can view their reports.', 'danger')
        return redirect(url_for('dashboard_ui.dashboard'))
    jwt_token = session.get('access_token')
    headers = {'Authorization': f'Bearer {jwt_token}'} if jwt_token else {}
    api_url = get_api_url('/reports')
    try:
        if api_url:
            resp = requests.get(api_url, headers=headers)
        else:
            client = current_app.test_client()
            resp = client.get('/reports', headers=headers)
        try:
            reports = resp.json() if resp.status_code == 200 else []
        except Exception:
            reports = []
    except Exception:
        reports = []
    return render_template('my_reports.html', reports=reports)
