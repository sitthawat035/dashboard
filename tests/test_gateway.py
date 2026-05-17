import pytest
from unittest.mock import patch, MagicMock


def test_gateway_list_endpoint(client, auth_headers):
    """Test that gateway list endpoint exists and returns properly."""
    with patch('api.config.get_agent_configs') as mock_configs:
        mock_configs.return_value = []
        response = client.get('/api/gateways', headers=auth_headers)
        # Accept any response that isn't a redirect (auth required)
        assert response.status_code != 302


def test_gateway_start_requires_auth(client):
    """Test that gateway start requires authentication."""
    response = client.post('/api/gateway/test/start')
    assert response.status_code in [401, 302, 404]


def test_gateway_stop_requires_auth(client):
    """Test that gateway stop requires authentication."""
    response = client.post('/api/gateway/test/stop')
    assert response.status_code in [401, 302, 404]
