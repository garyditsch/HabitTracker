"""Public routes for the dashboard."""

from flask import Blueprint, render_template, jsonify
from services import get_public_dashboard_data, get_cached, set_cached

# Create public blueprint
public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """
    Public dashboard - displays habit tracking visualizations.

    SECURITY: Only shows habits where is_public = True.
    Uses caching to reduce database load.
    """
    return render_template('public/dashboard.html')


@public_bp.route('/api/dashboard/data')
def dashboard_data():
    """
    API endpoint for dashboard data (JSON).

    SECURITY CRITICAL: Only returns public habits (is_public = True).
    Cached for 1 hour to reduce database load.

    Returns:
        JSON with habits, logs, streaks, and completion rates
    """
    # Check cache first
    cached_data = get_cached('public_dashboard_json')
    if cached_data:
        return jsonify(cached_data)

    # Fetch fresh data
    # SECURITY: get_public_dashboard_data only returns is_public=True habits
    dashboard = get_public_dashboard_data(days=30)

    # Cache the result
    set_cached('public_dashboard_json', dashboard)

    return jsonify(dashboard)
