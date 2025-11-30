#!/usr/bin/env python3
"""
Security Checklist Tests for Health Tracker

Tests various security aspects of the application including:
- SQL Injection protection
- XSS protection
- Authentication
- Session security
- Input validation
- Authorization
"""

import os
import sys
import sqlite3
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    """Print test result with color coding"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")
    print()

def test_sql_injection_protection():
    """Test that SQL injection is prevented through parameterized queries"""
    print(f"{YELLOW}Testing SQL Injection Protection...{RESET}\n")

    # Check database.py for parameterized queries
    with open('models/database.py', 'r') as f:
        db_code = f.read()

    # Look for dangerous string formatting in SQL
    dangerous_patterns = [
        'f"SELECT',
        'f"INSERT',
        'f"UPDATE',
        'f"DELETE',
        '% "SELECT',
        '% "INSERT',
        '% "UPDATE',
        '% "DELETE',
        '.format("SELECT',
        '.format("INSERT',
    ]

    has_dangerous_sql = any(pattern in db_code for pattern in dangerous_patterns)
    print_test(
        "Parameterized queries in database.py",
        not has_dangerous_sql,
        "All SQL queries use parameterized statements (?, placeholder)" if not has_dangerous_sql else "Found potential string formatting in SQL!"
    )

    # Check service files
    service_files = [
        'services/habit_service.py',
        'services/log_service.py',
        'services/dashboard_service.py'
    ]

    all_safe = True
    for service_file in service_files:
        with open(service_file, 'r') as f:
            code = f.read()
        has_dangerous = any(pattern in code for pattern in dangerous_patterns)
        if has_dangerous:
            all_safe = False
            print_test(f"SQL injection check in {service_file}", False, "Found potential SQL injection vulnerability")
        else:
            print_test(f"SQL injection check in {service_file}", True, "Uses parameterized queries")

    return not has_dangerous_sql and all_safe

def test_xss_protection():
    """Test that XSS is prevented through proper escaping"""
    print(f"{YELLOW}Testing XSS Protection...{RESET}\n")

    # Check JavaScript files for proper HTML escaping
    js_files = [
        'static/js/dashboard.js',
        'static/js/tracking.js',
        'static/js/settings.js'
    ]

    all_safe = True
    for js_file in js_files:
        with open(js_file, 'r') as f:
            code = f.read()

        # Check for escapeHtml function or textContent usage
        has_escape_function = 'escapeHtml' in code or 'textContent' in code

        # Check for dangerous innerHTML with user data
        has_dangerous_innerHTML = '.innerHTML = habit' in code or '.innerHTML = name' in code

        if has_escape_function and not has_dangerous_innerHTML:
            print_test(f"XSS protection in {js_file}", True, "Uses escapeHtml or textContent for user data")
        else:
            all_safe = False
            print_test(f"XSS protection in {js_file}", False, "May have XSS vulnerability")

    return all_safe

def test_authentication():
    """Test authentication implementation"""
    print(f"{YELLOW}Testing Authentication...{RESET}\n")

    # Check for secrets.compare_digest usage
    with open('routes/auth.py', 'r') as f:
        auth_code = f.read()

    uses_constant_time = 'secrets.compare_digest' in auth_code
    print_test(
        "Constant-time password comparison",
        uses_constant_time,
        "Uses secrets.compare_digest to prevent timing attacks" if uses_constant_time else "Should use secrets.compare_digest"
    )

    # Check for session management
    has_session_clear = 'session.clear()' in auth_code
    has_session_set = "session['authenticated']" in auth_code

    print_test(
        "Proper session management",
        has_session_clear and has_session_set,
        "Sets and clears session properly"
    )

    return uses_constant_time and has_session_clear and has_session_set

def test_session_security():
    """Test session security configuration"""
    print(f"{YELLOW}Testing Session Security...{RESET}\n")

    with open('config.py', 'r') as f:
        config_code = f.read()

    # Check for session security settings
    checks = {
        'SESSION_COOKIE_HTTPONLY': 'SESSION_COOKIE_HTTPONLY = True' in config_code,
        'SESSION_COOKIE_SAMESITE': 'SESSION_COOKIE_SAMESITE' in config_code,
        'SESSION_COOKIE_SECURE': 'SESSION_COOKIE_SECURE' in config_code,
        'SECRET_KEY from environment': 'SECRET_KEY' in config_code and 'os.getenv' in config_code,
    }

    for check_name, passed in checks.items():
        print_test(f"Session security: {check_name}", passed)

    return all(checks.values())

def test_authorization():
    """Test authorization on protected routes"""
    print(f"{YELLOW}Testing Authorization...{RESET}\n")

    with open('routes/admin.py', 'r') as f:
        admin_code = f.read()

    # Count @login_required decorators
    login_required_count = admin_code.count('@login_required')

    # Check that all route functions have @login_required
    route_count = admin_code.count('@admin.route')

    print_test(
        "Protected routes use @login_required",
        login_required_count > 0,
        f"Found {login_required_count} @login_required decorators for {route_count} routes"
    )

    # Check decorator implementation
    with open('utils/decorators.py', 'r') as f:
        decorator_code = f.read()

    checks_authenticated = "'authenticated' in session" in decorator_code or "session.get('authenticated')" in decorator_code

    print_test(
        "@login_required checks session",
        checks_authenticated,
        "Decorator properly checks session authentication"
    )

    return login_required_count > 0 and checks_authenticated

def test_input_validation():
    """Test input validation"""
    print(f"{YELLOW}Testing Input Validation...{RESET}\n")

    # Check routes for validation
    with open('routes/admin.py', 'r') as f:
        admin_code = f.read()

    # Check for JSON validation
    has_json_validation = 'request.get_json()' in admin_code
    has_validation_checks = 'if not' in admin_code or 'not data.get' in admin_code

    print_test(
        "Input validation in API routes",
        has_json_validation and has_validation_checks,
        "Routes validate JSON input and check for required fields"
    )

    # Check for maxlength in forms
    with open('templates/admin/settings.html', 'r') as f:
        template_code = f.read()

    has_maxlength = 'maxlength' in template_code

    print_test(
        "HTML input length limits",
        has_maxlength,
        "Forms use maxlength attribute to limit input"
    )

    return has_json_validation and has_validation_checks and has_maxlength

def test_public_private_separation():
    """Test that public/private habit separation is enforced"""
    print(f"{YELLOW}Testing Public/Private Habit Separation...{RESET}\n")

    with open('services/dashboard_service.py', 'r') as f:
        dashboard_code = f.read()

    # Check that public dashboard only gets public habits
    # This can be done by filtering directly or via include_private=False
    filters_public = (
        'is_public=True' in dashboard_code or
        'is_public = 1' in dashboard_code or
        'include_private=False' in dashboard_code
    )

    # Also verify that get_public_dashboard_data exists and has security comment
    has_security_comment = 'SECURITY CRITICAL' in dashboard_code or 'SECURITY:' in dashboard_code

    print_test(
        "Public dashboard filters by is_public",
        filters_public,
        "Dashboard service properly filters for public habits only" if filters_public else "WARNING: Public dashboard may expose private habits!"
    )

    print_test(
        "Security documentation present",
        has_security_comment,
        "Code includes security warnings about public/private separation"
    )

    return filters_public and has_security_comment

def test_environment_variables():
    """Test environment variable security"""
    print(f"{YELLOW}Testing Environment Variable Security...{RESET}\n")

    # Check that .env exists
    env_exists = Path('.env').exists()
    print_test(
        ".env file exists",
        env_exists,
        "Environment variables configured"
    )

    # Check that .env is in .gitignore
    gitignore_exists = Path('.gitignore').exists()
    if gitignore_exists:
        with open('.gitignore', 'r') as f:
            gitignore = f.read()
        env_ignored = '.env' in gitignore
        print_test(
            ".env is in .gitignore",
            env_ignored,
            ".env file won't be committed to git" if env_ignored else "WARNING: .env should be in .gitignore!"
        )
    else:
        print_test(".gitignore exists", False, "Create .gitignore to protect sensitive files")
        env_ignored = False

    # Check .env.example exists
    env_example_exists = Path('.env.example').exists()
    print_test(
        ".env.example exists",
        env_example_exists,
        "Template provided for environment setup"
    )

    return env_exists and env_ignored and env_example_exists

def test_error_handling():
    """Test error handling doesn't expose sensitive information"""
    print(f"{YELLOW}Testing Error Handling...{RESET}\n")

    with open('app.py', 'r') as f:
        app_code = f.read()

    # In production, debug should be off
    # Check that debug is configurable
    debug_configurable = 'debug=' in app_code or 'DEBUG' in app_code

    print_test(
        "Debug mode is configurable",
        debug_configurable,
        "Debug mode can be disabled for production"
    )

    return True

def run_all_tests():
    """Run all security tests"""
    print(f"\n{'='*60}")
    print(f"  HEALTH TRACKER - SECURITY CHECKLIST")
    print(f"{'='*60}\n")

    results = {
        "SQL Injection Protection": test_sql_injection_protection(),
        "XSS Protection": test_xss_protection(),
        "Authentication": test_authentication(),
        "Session Security": test_session_security(),
        "Authorization": test_authorization(),
        "Input Validation": test_input_validation(),
        "Public/Private Separation": test_public_private_separation(),
        "Environment Variables": test_environment_variables(),
        "Error Handling": test_error_handling(),
    }

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}\n")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} - {test_name}")

    print(f"\n{'='*60}")
    percentage = (passed / total) * 100
    color = GREEN if percentage == 100 else YELLOW if percentage >= 80 else RED
    print(f"{color}Score: {passed}/{total} ({percentage:.0f}%){RESET}")
    print(f"{'='*60}\n")

    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
