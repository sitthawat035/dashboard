import pytest
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create application fixture for testing."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Create authentication headers for API requests."""
    # Default test password from .env.example
    return {
        'Authorization': 'Bearer test_token',
        'Content-Type': 'application/json'
    }
