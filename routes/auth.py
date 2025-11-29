"""Authentication routes for login and logout."""

import secrets
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from config import Config
from utils.decorators import already_logged_in

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@already_logged_in
def login():
    """
    Login page and authentication handler.

    GET: Display login form
    POST: Verify password and set session
    """
    if request.method == 'POST':
        password = request.form.get('password', '')

        # SECURITY: Use constant-time comparison to prevent timing attacks
        if secrets.compare_digest(password, Config.APP_PASSWORD):
            # Set session as authenticated
            session['authenticated'] = True
            session.permanent = True  # Use permanent session (with timeout)

            # Redirect to next page or default to tracking interface
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('admin.track'))
        else:
            # Invalid password
            flash('Invalid password. Please try again.', 'error')
            return render_template('admin/login.html', error=True)

    # GET request - show login form
    return render_template('admin/login.html')


@auth_bp.route('/logout')
def logout():
    """
    Logout handler - clears session and redirects to public dashboard.
    """
    # Clear all session data
    session.clear()

    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('public.index'))
