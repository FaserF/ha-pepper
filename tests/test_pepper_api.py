# ruff: noqa: E402
"""Tests for Pepper API client."""
import sys
from unittest.mock import MagicMock

# Mock homeassistant modules to prevent import errors during collection
sys.modules['homeassistant'] = MagicMock()
sys.modules['homeassistant.const'] = MagicMock()
sys.modules['homeassistant.core'] = MagicMock()
sys.modules['homeassistant.config_entries'] = MagicMock()
sys.modules['homeassistant.helpers'] = MagicMock()
sys.modules['homeassistant.helpers.update_coordinator'] = MagicMock()
sys.modules['homeassistant.helpers.entity_platform'] = MagicMock()
sys.modules['homeassistant.components'] = MagicMock()
sys.modules['homeassistant.components.sensor'] = MagicMock()

import json
from unittest.mock import patch

import pytest

from custom_components.pepper.pepper_api import PepperAPI


@pytest.fixture
def api():
    """Create a PepperAPI instance."""
    return PepperAPI(platform="mydealz.de")

def test_fetch_session_success(api):
    """Test fetching session successfully."""
    mock_cookie = MagicMock()
    mock_cookie.name = "xsrf_t"
    mock_cookie.value = '"test_token"'

    with patch.object(api, "_cookie_jar", [mock_cookie]), \
         patch("urllib.request.OpenerDirector.open") as mock_open:

        mock_response = MagicMock()
        mock_response.read.return_value = b"<html></html>"
        mock_open.return_value.__enter__.return_value = mock_response

        api.fetch_session()

        assert api.xsrf_token == "test_token"

def test_fetch_session_failure(api):
    """Test fetching session error handling."""
    with patch("urllib.request.OpenerDirector.open", side_effect=Exception("Network error")):
        with pytest.raises(ConnectionError):
            api.fetch_session()

def test_get_deals_success(api):
    """Test retrieving and parsing deals list."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "threads": [
                {
                    "threadId": "12345",
                    "title": "Super Deal",
                    "url": "https://www.mydealz.de/deals/super-deal-12345",
                    "price": 9.99,
                    "temperature": 100.5,
                    "publishedAt": 1600000000,
                    "createdAt": 1599999900,
                    "description": "Very good deal",
                    "merchant": {
                        "merchantId": "99",
                        "merchantName": "SuperShop"
                    },
                    "mainImage": {
                        "uid": "12345_1.raw",
                        "path": "threads/raw/abc",
                        "name": "12345_1",
                        "ext": "raw"
                    }
                }
            ]
        }
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="hot")

        assert len(deals) == 1
        deal = deals[0]
        assert deal["id"] == "12345"
        assert deal["title"] == "Super Deal"
        assert deal["price"] == 9.99
        assert deal["temperature"] == 100.5
        assert deal["merchant"] == "SuperShop"
        assert deal["image_url"] == "https://static.mydealz.de/threads/raw/abc/12345_1/re/300x300/qt/60/12345_1.jpg"

def test_get_deals_graphql_error(api):
    """Test GraphQL error handling."""
    api.xsrf_token = "dummy_token"

    graphql_error_response = {
        "errors": [
            {
                "message": "Validation error"
            }
        ]
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_error_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        with pytest.raises(ValueError, match="GraphQL Query Error: Validation error"):
            api.get_deals()
