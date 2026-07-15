# ruff: noqa: E402
"""Tests for Pepper API client."""

import sys
from unittest.mock import MagicMock

# Mock homeassistant modules to prevent import errors during collection
sys.modules["homeassistant"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.components.sensor"] = MagicMock()

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

    with (
        patch.object(api, "_cookie_jar", [mock_cookie]),
        patch("urllib.request.OpenerDirector.open") as mock_open,
    ):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html></html>"
        mock_open.return_value.__enter__.return_value = mock_response

        api.fetch_session()

        assert api.xsrf_token == "test_token"


def test_fetch_session_failure(api):
    """Test fetching session error handling."""
    with patch(
        "urllib.request.OpenerDirector.open", side_effect=Exception("Network error")
    ):
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
                    "merchant": {"merchantId": "99", "merchantName": "SuperShop"},
                    "mainImage": {
                        "uid": "12345_1.raw",
                        "path": "threads/raw/abc",
                        "name": "12345_1",
                        "ext": "raw",
                    },
                }
            ]
        }
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="new")

        assert len(deals) == 1
        deal = deals[0]
        assert deal["id"] == "12345"
        assert deal["title"] == "Super Deal"
        assert deal["price"] == 9.99
        assert deal["temperature"] == 100.5
        assert deal["merchant"] == "SuperShop"
        assert (
            deal["image_url"]
            == "https://static.mydealz.de/threads/raw/abc/12345_1/re/300x300/qt/60/12345_1.jpg"
        )


def test_get_deals_hot_success(api):
    """Test retrieving and parsing hottestWidget deals list (sort_mode='hot')."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "hottestWidget": {
                "threads": [
                    {
                        "threadId": "54321",
                        "title": "Hottest Deal",
                        "url": "https://www.mydealz.de/deals/hottest-deal-54321",
                        "price": 19.99,
                        "temperature": 500.5,
                        "publishedAt": 1600000000,
                        "createdAt": 1599999900,
                        "description": "True hottest deal",
                        "merchant": {"merchantName": "HotShop"},
                        "mainImage": {
                            "path": "threads/raw/def",
                            "name": "54321_1",
                        },
                    }
                ]
            }
        }
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="hot")

        assert len(deals) == 1
        deal = deals[0]
        assert deal["id"] == "54321"
        assert deal["title"] == "Hottest Deal"
        assert deal["price"] == 19.99
        assert deal["temperature"] == 500.5
        assert deal["merchant"] == "HotShop"
        assert (
            deal["image_url"]
            == "https://static.mydealz.de/threads/raw/def/54321_1/re/300x300/qt/60/54321_1.jpg"
        )


def test_get_deals_graphql_error(api):
    """Test GraphQL error handling."""
    api.xsrf_token = "dummy_token"

    graphql_error_response = {"errors": [{"message": "Validation error"}]}

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_error_response).encode(
            "utf-8"
        )
        mock_open.return_value.__enter__.return_value = mock_response

        with pytest.raises(ValueError, match="GraphQL Query Error: Validation error"):
            api.get_deals()


def test_login_success(api):
    """Test login mutation call."""
    api.xsrf_token = "dummy_token"
    api.username = "FaserF"
    api.password = "secret"

    graphql_response = {
        "data": {
            "login": {
                "user": {
                    "userId": "123",
                    "username": "FaserF",
                }
            }
        }
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        api.login()
        # Successfully did not raise error


def test_get_user_profile_success(api):
    """Test get_user_profile query."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "me": {
                "userId": "123",
                "username": "FaserF",
                "karma": 1200,
                "notificationUnreadCount": 5,
                "unreadConversationsCount": 2,
            }
        }
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        profile = api.get_user_profile()
        assert profile["userId"] == "123"
        assert profile["username"] == "FaserF"
        assert profile["karma"] == 1200
        assert profile["notificationUnreadCount"] == 5
        assert profile["unreadConversationsCount"] == 2


def test_search_deals_success(api):
    """Test search_deals scraper."""
    html_content = """
    <html>
      <a class="cept-tt thread-link linkPlain thread-title--list js-thread-title"
         title="RTX 5080 Deal"
         href="https://www.mydealz.de/deals/rtx-5080-deal-1234">RTX 5080</a>
    </html>
    """

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = html_content.encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.search_deals("rtx")
        assert len(deals) == 1
        assert deals[0]["title"] == "RTX 5080 Deal"
        assert deals[0]["url"] == "https://www.mydealz.de/deals/rtx-5080-deal-1234"


def test_get_deals_with_filters(api):
    """Test get_deals with is_freebies and is_voucher filters."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "threads": [
                {
                    "threadId": "111",
                    "title": "Freebie Item",
                    "url": "https://www.mydealz.de/deals/freebie-111",
                    "price": 0.00,
                    "temperature": 300.0,
                    "publishedAt": 1600000000,
                    "createdAt": 1599999900,
                    "description": "Gratis",
                    "couponCode": "FREECODE",
                    "merchant": {"merchantName": "FreeShop"},
                    "mainImage": None,
                }
            ]
        }
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="new", is_freebies=True)
        assert len(deals) == 1
        assert deals[0]["price"] == 0.00
        assert deals[0]["coupon_code"] == "FREECODE"
