from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_jwt_extended import jwt_required, get_jwt
from utils.roles import government_required
import requests

users_ui = Blueprint('users_ui', __name__)

@users_ui.route('/debug')
def users_debug():
    return 'users_ui blueprint is loaded', 200
from utils.roles import government_required
import requests

users_ui = Blueprint('users_ui', __name__)

@users_ui.route('/users')
def users_management():
    import requests
    from flask import current_app, session, redirect, url_for, flash
    # Session-based access control
    if 'role' not in session or session['role'] != 'government':
        flash('Access denied. Government only.', 'danger')
        return redirect(url_for('dashboard_ui.dashboard'))
    jwt_token = session.get('access_token')
    api_url = current_app.config.get('API_URL', 'http://localhost:5001')
    headers = {'Authorization': f'Bearer {jwt_token}'} if jwt_token else {}
    try:
        resp = requests.get(f'{api_url}/users', headers=headers)
        users = resp.json() if resp.status_code == 200 else []
    except Exception:
        users = []
    return render_template('users_management.html', users=users)

@users_ui.route('/users/<int:user_id>', methods=['GET', 'POST'])
def user_detail(user_id):
    import requests
    from flask import current_app, session, redirect, url_for, flash
    # Session-based access control
    if 'role' not in session or session['role'] != 'government':
        flash('Access denied. Government only.', 'danger')
        return redirect(url_for('dashboard_ui.dashboard'))
    jwt_token = session.get('access_token')
    api_url = current_app.config.get('API_URL', 'http://localhost:5001')
    headers = {'Authorization': f'Bearer {jwt_token}'} if jwt_token else {}
    user = None
    error = None
    # Handle role change
    if request.method == 'POST':
        new_role = request.form.get('role')
        try:
            resp = requests.patch(f'{api_url}/users/{user_id}', json={'role': new_role}, headers=headers)
            if resp.status_code == 200:
                flash('Role updated successfully.', 'success')
            else:
                flash('Failed to update role: ' + resp.json().get('message', 'Unknown error'), 'danger')
        except Exception as e:
            flash('Error updating role: ' + str(e), 'danger')
    # Always fetch user detail
    try:
        resp = requests.get(f'{api_url}/users/{user_id}', headers=headers)
        if resp.status_code == 200:
            user = resp.json()
        else:
            error = 'User not found.'
    except Exception as e:
        error = str(e)
    return render_template('user_detail.html', user=user, error=error)
