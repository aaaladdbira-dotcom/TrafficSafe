from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import requests
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
        api_url = current_app.config.get('API_URL', 'http://localhost:5001')
        headers = {'Authorization': f'Bearer {jwt_token}'} if jwt_token else {}
        payload = {
            'date': date,
            'location': location,
            'delegation': delegation,
            'severity': severity,
            'phone': phone
        }
        try:
            print(f"[DEBUG UI] Submitting report to API: url={api_url}/reports, payload={payload}, headers={headers}")
            resp = requests.post(f'{api_url}/reports', json=payload, headers=headers)
            print(f"[DEBUG UI] API response: status_code={resp.status_code}, text={resp.text}")
            if resp.status_code == 201:
                flash('Report submitted successfully! Pending government verification.', 'success')
                return redirect(url_for('report_ui.my_reports'))
            else:
                msg = resp.json().get('description', 'Failed to submit report.')
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
    api_url = current_app.config.get('API_URL', 'http://localhost:5001')
    headers = {'Authorization': f'Bearer {jwt_token}'} if jwt_token else {}
    try:
        resp = requests.get(f'{api_url}/reports', headers=headers)
        reports = resp.json() if resp.status_code == 200 else []
    except Exception:
        reports = []
    return render_template('my_reports.html', reports=reports)
