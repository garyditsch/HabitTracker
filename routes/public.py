"""Public routes (temporary placeholder for Phase 4)."""

from flask import Blueprint

# Create public blueprint
public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """Temporary placeholder - will be replaced in Phase 4."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Health Tracker</title>
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
                background: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            a:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <h1>Health Tracker</h1>
        <p>Public dashboard coming in Phase 4...</p>
        <p><a href="/login">Login</a></p>
    </body>
    </html>
    '''
