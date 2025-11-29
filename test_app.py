"""Quick test to verify Flask app initializes correctly."""

from app import create_app

if __name__ == '__main__':
    print("Testing Flask app initialization...")

    app = create_app()

    print(f"✓ App created successfully")
    print(f"✓ App name: {app.name}")
    print(f"✓ Debug mode: {app.debug}")
    print(f"✓ Secret key configured: {bool(app.secret_key)}")

    # Test routes are registered
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"  {rule.endpoint:30s} {methods:10s} {rule.rule}")

    print("\n✓ Flask app initialization test successful!")
    print("\nYou can now run the app with: uv run python app.py")
    print("Or run in background: uv run flask run")
