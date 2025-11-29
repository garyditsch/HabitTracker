"""Authentication decorators for protecting routes."""

from functools import wraps
from flask import session, redirect, url_for, request, jsonify


def login_required(f):
    """
    Decorator to protect routes that require authentication.

    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return "This requires login"

    Behavior:
        - For HTML requests: Redirects to login page
        - For API/JSON requests: Returns 401 Unauthorized
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not session.get('authenticated'):
            # Check if this is an API request (JSON)
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'You must be logged in to access this resource'
                }), 401

            # For regular requests, redirect to login
            return redirect(url_for('auth.login', next=request.url))

        return f(*args, **kwargs)

    return decorated_function


def already_logged_in(f):
    """
    Decorator to redirect authenticated users away from login page.

    Usage:
        @app.route('/login')
        @already_logged_in
        def login():
            return "Login page"

    Behavior:
        - If user is authenticated, redirect to home/dashboard
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('authenticated'):
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)

    return decorated_function
