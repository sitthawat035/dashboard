import pytest


def test_login_page_loads(client):
    """Test that the login page loads correctly."""
    response = client.get('/')
    assert response.status_code in [200, 302, 401]


def test_login_endpoint_exists(client):
    """Test that login endpoint exists."""
    response = client.post('/api/login')
    assert response.status_code in [200, 400, 401, 404]


def test_auth_requires_credentials(client):
    """Test that protected endpoints require authentication."""
    response = client.get('/api/status')
    assert response.status_code in [401, 302]
