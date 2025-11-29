"""Admin routes (temporary placeholder for Phase 5)."""

from flask import Blueprint
from utils.decorators import login_required

# Create admin blueprint
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/track')
@login_required
def track():
    """Temporary placeholder - will be replaced in Phase 5."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Track - Health Tracker</title>
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                max-width: 600px;
                margin: 100px auto;
                padding: 20px;
                text-align: center;
            }
            h1 { color: #4CAF50; }
            a {
                display: inline-block;
                margin: 10px;
                padding: 10px 20px;
                background: #f44336;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            a:hover { background: #da190b; }
        </style>
    </head>
    <body>
        <h1>✓ Authentication Successful!</h1>
        <p>You are logged in.</p>
        <p>Tracking interface coming in Phase 5...</p>
        <p><a href="/logout">Logout</a></p>
    </body>
    </html>
    '''
