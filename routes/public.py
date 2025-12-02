"""Public routes for the dashboard."""

from flask import Blueprint, render_template, jsonify, request
from services import get_public_dashboard_data, get_yearly_heatmap_data, get_archived_habits_data, get_cached, set_cached

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


@public_bp.route('/api/dashboard/heatmap')
def heatmap_data():
    """
    API endpoint for yearly heatmap data (JSON).

    SECURITY CRITICAL: Only returns public habits (is_public = True).
    Cached for 1 hour to reduce database load.

    Query Parameters:
        year (optional): Year as integer (default: current year)

    Returns:
        JSON with yearly heatmap data showing daily completion percentages
    """
    # Get year parameter from query string
    year_param = request.args.get('year')

    # Validate and parse year
    year = None
    if year_param:
        try:
            year = int(year_param)
            # Validate year is reasonable (between 2000 and current year + 10)
            current_year = __import__('datetime').datetime.now().year
            if year < 2000 or year > current_year + 10:
                return jsonify({'error': 'Invalid year parameter'}), 400
        except ValueError:
            return jsonify({'error': 'Year must be an integer'}), 400

    # Create cache key based on year
    cache_key = f'heatmap_data_{year or "current"}'

    # Check cache first
    cached_data = get_cached(cache_key)
    if cached_data:
        return jsonify(cached_data)

    # Fetch fresh data
    # SECURITY: get_yearly_heatmap_data only returns is_public=True habits
    heatmap = get_yearly_heatmap_data(year=year)

    # Cache the result
    set_cached(cache_key, heatmap)

    return jsonify(heatmap)


@public_bp.route('/api/dashboard/archived')
def archived_habits():
    """
    API endpoint for archived habits data (JSON).

    SECURITY CRITICAL: Only returns public habits (is_public = True).

    Returns:
        JSON list of archived habits with lifetime statistics
    """
    # Check cache first
    cached_data = get_cached('archived_habits_data')
    if cached_data:
        return jsonify(cached_data)

    # Fetch fresh data
    # SECURITY: get_archived_habits_data only returns is_public=True habits
    archived = get_archived_habits_data()

    # Cache the result
    set_cached('archived_habits_data', archived)

    return jsonify(archived)
