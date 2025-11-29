Implementation Plan: Personal Health Tracker

 Overview

 Build a maintenance-free Flask web application for tracking daily
 health habits with a public dashboard and password-protected
 tracking interface.

 Project Structure

 HealthTracker/
 ├── app.py                      # Main Flask application entry
 ├── config.py                   # Configuration management
 ├── requirements.txt            # Python dependencies
 ├── .env.example               # Environment variable template
 ├── .gitignore                 # Git ignore rules
 │
 ├── models/
 │   ├── __init__.py
 │   ├── database.py            # Database connection &
 initialization
 │   └── schema.sql             # SQL schema definitions
 │
 ├── routes/
 │   ├── __init__.py
 │   ├── public.py              # Public dashboard routes
 │   ├── admin.py               # Protected tracking routes
 (SECURITY CRITICAL)
 │   └── auth.py                # Login/logout routes
 │
 ├── services/
 │   ├── __init__.py
 │   ├── habit_service.py       # Habit CRUD operations
 │   ├── log_service.py         # Log CRUD operations
 │   ├── dashboard_service.py   # Dashboard data aggregation
 │   └── cache_service.py       # Simple in-memory caching
 │
 ├── utils/
 │   ├── __init__.py
 │   └── decorators.py          # @login_required decorator
 │
 ├── templates/
 │   ├── base.html              # Base template
 │   ├── public/
 │   │   └── dashboard.html     # Public read-only dashboard
 │   └── admin/
 │       ├── login.html         # Login page
 │       ├── track.html         # Daily tracking interface
 │       └── settings.html      # Habit management
 │
 ├── static/
 │   ├── css/
 │   │   └── custom.css         # Minimal custom styles
 │   └── js/
 │       ├── dashboard.js       # Chart.js initialization
 │       └── tracking.js        # Tracking UI interactions
 │
 └── instance/
     └── tracker.db             # SQLite database (gitignored)

 Database Schema

 habits table

 - id (INTEGER, PRIMARY KEY)
 - name (TEXT, NOT NULL)
 - is_active (BOOLEAN, DEFAULT 1) - Soft delete flag
 - is_public (BOOLEAN, DEFAULT 1) - Public dashboard visibility
 - order_index (INTEGER, DEFAULT 0) - Custom ordering for display
 - created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

 logs table

 - id (INTEGER, PRIMARY KEY)
 - habit_id (INTEGER, FOREIGN KEY → habits.id, ON DELETE CASCADE)
 - date (DATE, NOT NULL)
 - status (BOOLEAN, NOT NULL)
 - UNIQUE(habit_id, date) - Prevent duplicate entries

 Indexes

 - idx_logs_date ON logs(date)
 - idx_logs_habit_date ON logs(habit_id, date)
 - idx_habits_public ON habits(is_public, is_active)

 Implementation Phases

 Phase 0: Project Initialization

 Goal: Set up development environment

 1. Initialize Git repository with .gitignore
 2. Create requirements.txt:
   - Flask==3.0.0
   - python-dotenv==1.0.0
   - gunicorn==21.2.0 (for production)
 3. Create .env.example and actual .env with:
   - APP_PASSWORD - Authentication password
   - SECRET_KEY - Flask session secret (32+ random bytes)
   - FLASK_ENV - development/production
   - DATABASE_PATH - instance/tracker.db
 4. Create config.py to load environment variables

 Phase 1: Database Layer

 Goal: Establish data persistence

 1. Create models/schema.sql with table definitions and indexes
 2. Create models/database.py:
   - Database connection context manager
   - Table creation from schema.sql
   - Database initialization function
 3. Test: Database initializes with correct schema

 Phase 2: Service Layer

 Goal: Encapsulate business logic

 1. services/habit_service.py:
   - get_all_habits(include_private=False) - Critical: defaults to 
 public only
   - get_active_habits(include_private=True) - Returns habits
 ordered by order_index
   - create_habit(name, is_public=True) - Auto-assigns next
 order_index
   - update_habit(habit_id, **kwargs) - Includes order_index
 updates
   - reorder_habits(habit_ids) - Updates order_index for multiple
 habits
   - delete_habit(habit_id) - Soft delete
 2. services/log_service.py:
   - get_logs_for_date(date, include_private=True)
   - get_logs_for_habit(habit_id, start_date, end_date)
   - upsert_log(habit_id, date, status) - Insert or update
   - get_habit_streak(habit_id) - Calculate current streak
 3. services/dashboard_service.py:
   - get_public_dashboard_data() - Must filter is_public=True
   - Returns: public habits, last 30 days of logs, streaks,
 completion %
 4. services/cache_service.py:
   - Simple in-memory dict with timestamp expiration
   - get_cached(key), set_cached(key, value, duration),
 invalidate_cache(key)
   - Cache dashboard data for 1 hour

 Phase 3: Authentication

 Goal: Implement secure password authentication

 1. Create utils/decorators.py:
   - @login_required decorator
   - Checks Flask session for authentication
   - Redirects to login or returns 401 for API calls
 2. Create routes/auth.py:
   - GET /login - Render login form
   - POST /login - Verify password with secrets.compare_digest(),
 set session
   - GET /logout - Clear session
 3. Configure Flask session security in app.py:
   - SESSION_COOKIE_HTTPONLY = True
   - SESSION_COOKIE_SECURE = True (production)
   - SESSION_COOKIE_SAMESITE = 'Lax'

 Phase 4: Public Routes

 Goal: Build publicly accessible dashboard

 1. Create routes/public.py:
   - GET / - Render dashboard (check cache first)
   - GET /api/dashboard/data - JSON for Chart.js
   - Security: Must filter to is_public=True habits only
   - Invalidate cache on any log creation/update
 2. Create templates/public/dashboard.html:
   - Hero section with title
   - Responsive grid of habit cards
   - Each card: name, 30-day chart, streak, completion %
   - Subtle "Login" link in footer
 3. Create static/js/dashboard.js:
   - Fetch data from /api/dashboard/data
   - Initialize Chart.js line graphs
   - Responsive, mobile-friendly charts

 Phase 5: Protected Routes

 Goal: Build tracking interface

 1. Create routes/admin.py - All routes use @login_required:
   - GET /track?date=YYYY-MM-DD - Daily tracking (default: today)
   - POST /api/track/save - Save entire day's logs, invalidate
 cache
   - GET /settings - Habit management
   - POST /api/habits - Create habit
   - PUT /api/habits/<id> - Update habit
   - POST /api/habits/reorder - Update order_index for drag-drop
 reordering
   - DELETE /api/habits/<id> - Soft delete habit
 2. Create templates/admin/track.html:
   - Current date display
   - Date navigation (Previous | Today | Next)
   - List of active habits with large toggle buttons
   - Visual feedback for completed state
   - "Save Day" button
   - Mobile-first design (44px+ touch targets)
 3. Create templates/admin/settings.html:
   - Form to add new habit (name + public checkbox)
   - List of habits with drag handles for reordering
   - Edit/delete/toggle actions for each habit
   - Confirmation for deletions
   - Visual feedback during drag operations
 4. Create static/js/tracking.js:
   - Toggle interactions for habit checkboxes
   - Save button handler with error handling
   - Date navigation logic
   - Visual feedback for save success/failure
 5. Create static/js/settings.js:
   - Drag-and-drop functionality for habit reordering
   - Save reordered list to /api/habits/reorder
   - Inline editing for habit properties
   - Delete confirmations

 Phase 6: Frontend Polish

 Goal: Create cohesive UI

 1. Create templates/base.html:
   - TailwindCSS CDN: <script 
 src="https://cdn.tailwindcss.com"></script>
   - Chart.js CDN for dashboard pages
   - Responsive meta tags
   - Flash message support
   - Block system: title, content, scripts
 2. Apply consistent styling:
   - Color scheme: Green (completion), Gray (neutral), Blue
 (interactive)
   - Responsive design with Tailwind classes
   - Ensure 44px+ touch targets
   - Accessible HTML (semantic elements, labels, ARIA where needed)

 Phase 7: Security & Testing

 Goal: Validate security and functionality

 Security Checklist:
 - /track redirects to login when not authenticated
 - API endpoints return 401 without valid session
 - Private habits don't appear in /api/dashboard/data
 - SQL injection attempts are prevented (parameterized queries)
 - Session cookies have secure flags
 - Password comparison uses secrets.compare_digest()

 Functionality Testing:
 - Create public and private habits
 - Log habits for multiple dates
 - Verify dashboard shows only public habits
 - Test date navigation
 - Verify cache invalidation
 - Test habit editing/deletion
 - Verify streak calculations

 Phase 8: Deployment

 Goal: Deploy to production

 1. Set up server (VPS or cloud provider)
 2. Install Python 3.9+, create virtual environment
 3. Install dependencies from requirements.txt
 4. Configure environment variables in .env
 5. Initialize database
 6. Set up Gunicorn: gunicorn -w 4 -b 127.0.0.1:8000 app:app
 7. Configure Nginx reverse proxy
 8. Install SSL with Let's Encrypt: sudo certbot --nginx -d 
 tracker.garyditsch.com
 9. Create systemd service for auto-restart
 10. Test production deployment

 Critical Security Requirements

 Database Layer

 - Use parameterized queries exclusively (prevent SQL injection)
 - Set instance/tracker.db permissions to 600
 - Regular backups via cron job

 Authentication Layer

 - CRITICAL: Every write endpoint must check session authentication
 - Use secrets.compare_digest() for password comparison (prevent
 timing attacks)
 - Strong SECRET_KEY (32+ random bytes)
 - Secure session cookie flags

 Public Dashboard

 - CRITICAL: SQL queries must filter is_public=True
 - Double-check no private data in JSON responses
 - Cache invalidation on any data modification

 Deployment

 - HTTPS only (redirect HTTP → HTTPS)
 - Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
 - Firewall configuration (only ports 80/443 open)
 - Regular security updates

 Technical Decisions

 TailwindCSS: CDN

 - Rationale: No build step = simpler deployment, maintenance-free
 - Use CDN link in base.html
 - Minimal custom CSS

 Session Management: Flask Built-in Sessions

 - Rationale: Simple, no external dependencies needed for
 single-user app
 - Client-side sessions with secure cookies
 - Strong SECRET_KEY from environment

 Caching: In-Memory Dictionary

 - Rationale: Sufficient for single-user, low-traffic app
 - Cache dashboard data for 1 hour
 - Invalidate on any habit/log modification
 - Can upgrade to Redis later if needed

 Save Mechanism: Explicit "Save Day" Button

 - Rationale: Intentional action, simpler error handling, fewer API
  calls
 - Clearer user feedback for save success/failure
 - Batch operation reduces server load

 Database: SQLite with Indexes

 - Rationale: Perfect for single-user, embedded database
 - Indexes on date, habit_id, is_public for query performance
 - ON DELETE CASCADE for automatic log cleanup

 Files Critical for Implementation

 1. app.py - Main entry point, Flask initialization, blueprint
 registration
 2. models/database.py - Database connection and initialization
 3. routes/admin.py - Protected routes with authentication checks
 (SECURITY CRITICAL)
 4. services/dashboard_service.py - Data aggregation with is_public
  filtering (SECURITY CRITICAL)
 5. utils/decorators.py - @login_required decorator (SECURITY
 CRITICAL)

 Implementation Order (Working Increments)

 1. Core Framework (Days 1-2): Basic Flask app, database
 initialization with order_index
 2. Authentication (Day 3): Login/logout working
 3. Habit Management (Days 4-5): CRUD for habits + drag-to-reorder
 functionality
 4. Tracking Interface (Days 6-7): Daily logging with explicit save
  button
 5. Public Dashboard (Days 8-9): Charts and visualizations
 6. Polish & Security (Day 10): Testing, mobile responsive, error
 handling
 7. Deployment (Day 11): Traditional VPS deployment with Gunicorn +
  Nginx + HTTPS

 Features Included Beyond PRD

 1. Habit Ordering: Drag-to-reorder functionality with order_index
 column
   - Provides better control over habit display order
   - Drag handles in settings page
   - Order persists across tracking interface

 Future Enhancements (Post-Launch)

 1. Data Export: CSV/JSON download of all logs (can be added later
 based on need)
 2. Enhanced Analytics: Best streak ever, monthly stats
 3. Error Recovery: Friendly error messages, retry logic
 4. Basic Logging: Python logging for errors and auth failures
 5. Future Date Prevention: Block logging for dates after today

 Next Steps

 Once plan is approved, implementation will begin with Phase 0
 (project initialization) and proceed through phases sequentially,
 ensuring working increments at each stage.