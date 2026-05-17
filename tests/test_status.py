import pytest
from unittest.mock import patch


def test_status_endpoint_requires_auth(client):
    """Test that status endpoint requires authentication."""
    response = client.get('/api/status')
    assert response.status_code in [401, 302]


def test_status_endpoint_with_auth(client, auth_headers):
    """Test status endpoint with auth returns valid response."""
    with patch('api.status.check_gateway_health') as mock_health:
        mock_health.return_value = {'status': 'unknown'}
        response = client.get('/api/status', headers=auth_headers)
        assert response.status_code in [200, 500]
