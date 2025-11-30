# Health Tracker

A personal habit tracking application with a public dashboard and password-protected admin interface. Built with Flask, SQLite, TailwindCSS, and Chart.js.

![Security Tests](https://img.shields.io/badge/security-100%25-brightgreen)
![Functionality Tests](https://img.shields.io/badge/tests-100%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Flask](https://img.shields.io/badge/flask-3.0.0-blue)

## Features

### Public Dashboard
- **Habit Visualization**: 30-day completion charts for all public habits
- **Statistics**: Current streak, completion rate, and total days tracked
- **Responsive Design**: Mobile-friendly interface with TailwindCSS
- **No Authentication Required**: Publicly accessible habit tracking data

### Admin Interface (Password Protected)
- **Daily Tracking**: Simple toggle interface for marking habits as complete
- **Date Navigation**: Track habits for any date (past, present, or future)
- **Habit Management**: Create, edit, delete, and reorder habits with drag-and-drop
- **Public/Private Toggle**: Control which habits appear on the public dashboard
- **Batch Save**: Save all daily habit completions in one action

### Technical Features
- **Security First**: SQL injection protection, XSS prevention, CSRF protection
- **Session Management**: Secure cookies with HttpOnly, SameSite, and Secure flags
- **Caching**: In-memory caching for dashboard data (1-hour TTL)
- **Accessibility**: WCAG 2.1 compliant with ARIA labels, skip navigation, and keyboard support
- **Database**: SQLite with optimized indexes for fast queries
- **Modern Python**: Built with `uv` for fast, reliable dependency management

---

## Quick Start

### Prerequisites
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/HealthTracker.git
   cd HealthTracker
   ```

2. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Create virtual environment and install dependencies**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set your SECRET_KEY and APP_PASSWORD
   ```

5. **Initialize the database**
   ```bash
   uv run python -c "from models import init_database; init_database()"
   ```

6. **Seed with sample data** (optional)
   ```bash
   uv run python seed_data.py
   ```

7. **Run the application**
   ```bash
   uv run python app.py
   ```

8. **Open in browser**
   - Public Dashboard: http://localhost:5001
   - Admin Login: http://localhost:5001/login

---

## Project Structure

```
HealthTracker/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── seed_data.py               # Sample data generator
│
├── models/                    # Database layer
│   ├── __init__.py
│   ├── database.py            # Database connection & queries
│   └── schema.sql             # SQLite schema definition
│
├── services/                  # Business logic layer
│   ├── habit_service.py       # Habit CRUD operations
│   ├── log_service.py         # Log tracking & streaks
│   ├── dashboard_service.py   # Data aggregation
│   └── cache_service.py       # In-memory caching
│
├── routes/                    # HTTP route handlers
│   ├── public.py              # Public dashboard routes
│   ├── admin.py               # Protected admin routes
│   └── auth.py                # Login/logout routes
│
├── utils/                     # Utilities
│   └── decorators.py          # @login_required decorator
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base template
│   ├── public/
│   │   └── dashboard.html     # Public dashboard
│   └── admin/
│       ├── login.html         # Login page
│       ├── track.html         # Daily tracking interface
│       └── settings.html      # Habit management
│
├── static/                    # Static assets
│   ├── js/
│   │   ├── dashboard.js       # Dashboard Chart.js logic
│   │   ├── tracking.js        # Daily tracking interface
│   │   └── settings.js        # Habit management & drag-drop
│   └── images/
│       └── favicon.svg        # App icon
│
├── instance/                  # Runtime data (gitignored)
│   └── healthtracker.db       # SQLite database
│
├── tests/                     # Test suites
│   ├── test_security.py       # Security checklist (9/9 passing)
│   └── test_functionality.py  # Functionality tests (7/7 passing)
│
├── .env                       # Environment variables (gitignored)
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── pyproject.toml             # Python dependencies
├── README.md                  # This file
├── DEPLOYMENT.md              # Deployment guide
└── todo.md                    # Development checklist
```

---

## Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────┐
│           Routes Layer                  │
│  (HTTP handlers, request/response)      │
│  • public.py  • admin.py  • auth.py     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Service Layer                   │
│  (Business logic, data aggregation)     │
│  • habit_service.py  • log_service.py   │
│  • dashboard_service.py  • cache.py     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          Data Layer                     │
│  (Database access, SQL queries)         │
│  • database.py  • schema.sql            │
└─────────────────────────────────────────┘
```

### Key Design Patterns

- **Separation of Concerns**: Routes, business logic, and data access are isolated
- **Service Layer**: All business logic centralized in service modules
- **Repository Pattern**: Database class encapsulates all SQL operations
- **Decorator Pattern**: `@login_required` for route protection
- **Factory Pattern**: Application creation in `app.py`
- **Caching Strategy**: In-memory cache with TTL for dashboard data

---

## API Endpoints

### Public Endpoints
- `GET /` - Public dashboard (HTML)
- `GET /api/dashboard/data` - Dashboard data (JSON, cached)

### Authentication
- `GET /login` - Login page (HTML)
- `POST /login` - Authenticate user
- `GET /logout` - End session

### Protected Endpoints (Require Authentication)
- `GET /track?date=YYYY-MM-DD` - Daily tracking interface (HTML)
- `GET /api/track/data?date=YYYY-MM-DD` - Tracking data (JSON)
- `POST /api/track/save` - Save day's habit completions
- `GET /settings` - Habit management interface (HTML)
- `GET /api/habits` - Get all habits (JSON)
- `POST /api/habits` - Create new habit
- `PUT /api/habits/<id>` - Update habit
- `DELETE /api/habits/<id>` - Soft delete habit
- `POST /api/habits/reorder` - Update habit order

---

## Security

This application implements security best practices:

### ✅ Security Checklist (100% Pass Rate)

- **SQL Injection Protection**: All queries use parameterized statements
- **XSS Prevention**: User input sanitized with `escapeHtml()` and `textContent`
- **Authentication**: Constant-time password comparison (`secrets.compare_digest`)
- **Session Security**: HttpOnly, SameSite=Lax, Secure (in production) cookies
- **Authorization**: `@login_required` decorator on all admin routes
- **Input Validation**: Server-side validation on all API endpoints
- **Public/Private Separation**: Dashboard only shows habits where `is_public=True`
- **Environment Variables**: Sensitive data (SECRET_KEY, passwords) in `.env`
- **CSRF Protection**: Flask session-based CSRF protection

### Security Headers (Nginx)
```nginx
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

---

## Testing

### Run Security Tests
```bash
python test_security.py
```

**Result**: 9/9 tests passing (100%)

### Run Functionality Tests
```bash
uv run python test_functionality.py
```

**Result**: 7/7 tests passing (100%)

### Test Coverage
- Database initialization and schema creation
- Habit CRUD operations
- Log tracking and streak calculation
- Dashboard data aggregation
- Cache functionality and expiration
- Habit reordering (drag-and-drop)
- Date handling (past, present, future)

---

## Development

### Running in Development Mode

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with auto-reload
uv run python app.py
```

Access at: http://localhost:5001

### Database Management

**Initialize/Reset Database**:
```bash
uv run python -c "from models import init_database; init_database()"
```

**Generate Sample Data**:
```bash
uv run python seed_data.py
```

**Backup Database**:
```bash
cp instance/healthtracker.db instance/healthtracker_backup.db
```

### Code Style

- **PEP 8 compliant** Python code
- **Docstrings** for all functions and classes
- **Type hints** where appropriate
- **Security comments** on critical sections

---

## Deployment

For production deployment instructions, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

Deployment guide covers:
- VPS setup (Ubuntu/Debian)
- Gunicorn configuration
- Nginx reverse proxy
- SSL/HTTPS with Let's Encrypt
- Systemd service setup
- Database backups
- Monitoring and maintenance

---

## Configuration

### Environment Variables (`.env`)

```bash
# Flask Environment
FLASK_ENV=development  # Set to 'production' for deployment

# Security (REQUIRED)
SECRET_KEY=your-secret-key-here-minimum-32-characters
APP_PASSWORD=your-admin-password-here

# Database
DATABASE_PATH=instance/healthtracker.db
```

**Generate SECRET_KEY**:
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

---

## Browser Support

- **Modern browsers**: Chrome, Firefox, Safari, Edge (last 2 versions)
- **Mobile**: iOS Safari 13+, Chrome Android
- **Accessibility**: WCAG 2.1 Level AA compliant

---

## Technologies Used

### Backend
- **Flask 3.0.0** - Web framework
- **SQLite** - Database
- **Gunicorn** - WSGI server (production)
- **python-dotenv** - Environment variable management

### Frontend
- **TailwindCSS** (CDN) - Styling
- **Chart.js 4.4.0** - Data visualization
- **Vanilla JavaScript** - Client-side interactivity

### DevOps
- **uv** - Fast Python package manager
- **Nginx** - Reverse proxy
- **Certbot** - SSL certificate management
- **Systemd** - Service management

---

## Roadmap

Future enhancements (not currently planned):
- [ ] CSV/JSON export of habit data
- [ ] Weekly/monthly statistics view
- [ ] Habit notes and descriptions
- [ ] Mobile PWA support
- [ ] Email reminders
- [ ] Multi-user support with user accounts

---

## Contributing

This is a personal project, but suggestions and bug reports are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License

Copyright (c) 2024 Health Tracker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Styled with [TailwindCSS](https://tailwindcss.com/)
- Charts powered by [Chart.js](https://www.chartjs.org/)
- Package management by [uv](https://github.com/astral-sh/uv)

---

**Questions or Issues?** Check the [DEPLOYMENT.md](DEPLOYMENT.md) guide or open an issue on GitHub.
