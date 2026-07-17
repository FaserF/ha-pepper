# ruff: noqa: E402
"""Tests for Pepper API client connection, auth, and queries."""

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
sys.modules["homeassistant.helpers.device_registry"] = MagicMock()
sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.components.sensor"] = MagicMock()
sys.modules["homeassistant.components.binary_sensor"] = MagicMock()
sys.modules["voluptuous"] = MagicMock()

import json
from unittest.mock import patch

import pytest

from custom_components.pepper.pepper_api import PepperAPI


@pytest.fixture
def api() -> PepperAPI:
    """Create a PepperAPI instance."""
    return PepperAPI(platform="mydealz.de")


@pytest.fixture
def api_with_auth() -> PepperAPI:
    """Create a PepperAPI instance with credentials."""
    return PepperAPI(platform="mydealz.de", username="FaserF", password="secret")


def test_fetch_session_success(api: PepperAPI) -> None:
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


def test_fetch_session_failure(api: PepperAPI) -> None:
    """Test fetching session error handling."""
    with patch(
        "urllib.request.OpenerDirector.open", side_effect=Exception("Network error")
    ):
        with pytest.raises(ConnectionError):
            api.fetch_session()


def test_login_uses_loginUser_mutation(api_with_auth: PepperAPI) -> None:
    """Test that login uses the updated loginUser mutation and LoginUserInput type."""
    api_with_auth.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "loginUser": {
                "user": {
                    "userId": "249802",
                    "username": "FaserF",
                }
            }
        }
    }

    captured_payload: dict = {}

    def mock_open_impl(req, timeout=None):
        nonlocal captured_payload
        data_bytes = req.data
        if data_bytes:
            captured_payload = json.loads(data_bytes.decode("utf-8"))
        res = MagicMock()
        res.__enter__.return_value = res
        res.read.return_value = json.dumps(graphql_response).encode("utf-8")
        return res

    with patch("urllib.request.OpenerDirector.open", side_effect=mock_open_impl):
        api_with_auth.login()

    assert "mutation login" in captured_payload.get("query", "")
    assert "$input: LoginUserInput!" in captured_payload.get("query", "")
    variables = captured_payload.get("variables", {})
    assert variables["input"]["identity"] == "FaserF"
    assert variables["input"]["password"] == "secret"


def test_login_no_credentials_is_noop(api: PepperAPI) -> None:
    """Test that login is a no-op if credentials are not configured."""
    api.xsrf_token = "dummy_token"
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        api.login()
        mock_open.assert_not_called()


def test_get_deals_new_mode_full_fields(api: PepperAPI) -> None:
    """Test fetching deals in new mode query with updated Thread fields."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "threads": [
                {
                    "threadId": "12345",
                    "title": "Test Title",
                    "url": "https://www.mydealz.de/deals/test-deal",
                    "price": 19.99,
                    "nextBestPrice": 29.99,
                    "temperature": 120.5,
                    "publishedAt": 1700000000,
                    "createdAt": 1699999900,
                    "pickedAt": 1700000100,
                    "description": "Deal description text",
                    "voucherCode": "SAVE10",
                    "type": "Deal",
                    "status": "Activated",
                    "isExpired": False,
                    "expirable": True,
                    "commentCount": 5,
                    "shareCount": 12,
                    "mainImage": {"path": "images/deals", "name": "deal123"},
                    "merchant": {
                        "merchantId": "99",
                        "merchantName": "Amazon",
                        "merchantPageUrl": "https://www.mydealz.de/händler/amazon",
                        "merchantUrlName": "amazon",
                    },
                    "user": {
                        "userId": "1001",
                        "username": "TestUser",
                    },
                    "groups": [
                        {
                            "groupsPath": [
                                {"pageUrl": "https://www.mydealz.de/gruppe/gaming"}
                            ]
                        }
                    ],
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
        d = deals[0]
        assert d["id"] == "12345"
        assert d["title"] == "Test Title"
        assert d["url"] == "https://www.mydealz.de/deals/test-deal"
        assert d["price"] == 19.99
        assert d["next_best_price"] == 29.99
        assert d["temperature"] == 120.5
        assert d["published_at"] == 1700000000
        assert d["created_at"] == 1699999900
        assert d["picked_at"] == 1700000100
        assert d["description"] == "Deal description text"
        assert d["voucher_code"] == "SAVE10"
        assert d["type"] == "Deal"
        assert d["status"] == "Activated"
        assert d["is_expired"] is False
        assert d["expirable"] is True
        assert d["comment_count"] == 5
        assert d["share_count"] == 12
        assert (
            d["image_url"]
            == "https://static.mydealz.de/images/deals/deal123/re/300x300/qt/60/deal123.jpg"
        )
        assert d["merchant"] == "Amazon"
        assert d["merchant_id"] == "99"
        assert d["merchant_page_url"] == "https://www.mydealz.de/händler/amazon"
        assert d["merchant_url_name"] == "amazon"
        assert d["submitter_id"] == "1001"
        assert d["submitter"] == "TestUser"
        assert d["groups"] == ["Gaming"]


def test_get_deals_hot_mode(api: PepperAPI) -> None:
    """Test fetching deals using hot widget query."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "hottestWidget": {
                "threads": [
                    {
                        "threadId": "12345",
                        "title": "Hottest Title",
                        "url": "https://www.mydealz.de/deals/hottest-deal",
                        "price": 0.0,
                        "nextBestPrice": 0.0,
                        "temperature": 500.0,
                        "publishedAt": 1700000000,
                        "createdAt": 1699999900,
                        "pickedAt": 0,
                        "description": "Freebie",
                        "voucherCode": None,
                        "type": "Freebie",
                        "status": "Activated",
                        "isExpired": False,
                        "expirable": False,
                        "commentCount": 10,
                        "shareCount": 50,
                        "mainImage": None,
                        "merchant": None,
                        "user": None,
                        "groups": [],
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
        assert deals[0]["title"] == "Hottest Title"
        assert deals[0]["temperature"] == 500.0


def test_get_deals_voucher_code_field_name(api: PepperAPI) -> None:
    """Test that GraphQL query uses the correct voucherCode field name."""
    api.xsrf_token = "dummy_token"

    captured_payload: dict = {}

    def mock_open_impl(req, timeout=None):
        nonlocal captured_payload
        captured_payload = json.loads(req.data.decode("utf-8"))
        res = MagicMock()
        res.__enter__.return_value = res
        res.read.return_value = json.dumps({"data": {"threads": []}}).encode("utf-8")
        return res

    with patch("urllib.request.OpenerDirector.open", side_effect=mock_open_impl):
        api.get_deals(sort_mode="new")

    query_str = captured_payload.get("query", "")
    assert "voucherCode" in query_str
    assert "couponCode" not in query_str


def test_get_deals_no_image(api: PepperAPI) -> None:
    """Test get_deals fallback when mainImage is missing or incomplete."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "threads": [
                {
                    "threadId": "1",
                    "title": "No Image Deal",
                    "mainImage": None,
                },
                {
                    "threadId": "2",
                    "title": "Incomplete Image Deal",
                    "mainImage": {"path": None, "name": "deal1"},
                },
            ]
        }
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="new")

        assert len(deals) == 2
        assert deals[0]["image_url"] is None
        assert deals[1]["image_url"] is None


def test_get_deals_no_merchant(api: PepperAPI) -> None:
    """Test get_deals fallback when merchant is missing or None."""
    api.xsrf_token = "dummy_token"
    graphql_response = {
        "data": {
            "threads": [
                {
                    "threadId": "1",
                    "merchant": None,
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
        assert deals[0]["merchant"] is None
        assert deals[0]["merchant_id"] is None


def test_get_deals_no_user(api: PepperAPI) -> None:
    """Test get_deals fallback when user is missing or None."""
    api.xsrf_token = "dummy_token"
    graphql_response = {
        "data": {
            "threads": [
                {
                    "threadId": "1",
                    "user": None,
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
        assert deals[0]["submitter"] is None
        assert deals[0]["submitter_id"] is None


def test_get_deals_freebies_filter(api: PepperAPI) -> None:
    """Test client-side filtering for freebies."""
    api.xsrf_token = "dummy_token"
    graphql_response = {
        "data": {
            "threads": [
                {"threadId": "1", "price": 0.0, "type": "Deal"},
                {"threadId": "2", "price": 10.0, "type": "Freebie"},
                {"threadId": "3", "price": 10.0, "type": "Deal"},
            ]
        }
    }
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="new", is_freebies=True)
        assert len(deals) == 2
        assert deals[0]["id"] == "1"
        assert deals[1]["id"] == "2"


def test_get_deals_voucher_filter(api: PepperAPI) -> None:
    """Test voucher filter query variables validation."""
    api.xsrf_token = "dummy_token"
    captured_payload: dict = {}

    def mock_open_impl(req, timeout=None):
        nonlocal captured_payload
        captured_payload = json.loads(req.data.decode("utf-8"))
        res = MagicMock()
        res.__enter__.return_value = res
        res.read.return_value = json.dumps({"data": {"threads": []}}).encode("utf-8")
        return res

    with patch("urllib.request.OpenerDirector.open", side_effect=mock_open_impl):
        api.get_deals(sort_mode="new", is_voucher=True)

    variables = captured_payload.get("variables", {})
    assert variables["filter"]["type"]["eq"] == "Voucher"


def test_get_deals_graphql_error(api: PepperAPI) -> None:
    """Test get_deals raises ValueError on GraphQL errors list."""
    api.xsrf_token = "dummy_token"
    graphql_response = {
        "errors": [{"message": "Access Denied"}],
        "data": None,
    }
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        with pytest.raises(ValueError, match="Access Denied"):
            api.get_deals(sort_mode="new")


def test_get_user_profile_new_fields(api: PepperAPI) -> None:
    """Test fetching logged-in user profile with updated API schema fields."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "me": {
                "userId": "249802",
                "username": "FaserF",
                "email": "seitzf1@yahoo.de",
                "createdAt": 1390000000,
                "threadCount": 66,
                "commentCount": 1803,
                "avatar": {
                    "path": "users/raw/default",
                    "name": "249802_1",
                },
                "badges": [
                    {"badgeId": "gold_badge"},
                ],
            }
        }
    }

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        profile = api.get_user_profile()

        assert profile["userId"] == "249802"
        assert profile["username"] == "FaserF"
        assert profile["email"] == "seitzf1@yahoo.de"
        assert profile["createdAt"] == 1390000000
        assert profile["threadCount"] == 66
        assert profile["commentCount"] == 1803
        assert profile["avatar"]["path"] == "users/raw/default"
        assert len(profile["badges"]) == 1


def test_get_user_profile_query_excludes_deprecated_fields(api: PepperAPI) -> None:
    """Test that get_user_profile query does not include obsolete schema fields."""
    api.xsrf_token = "dummy_token"
    captured_payload: dict = {}

    def mock_open_impl(req, timeout=None):
        nonlocal captured_payload
        captured_payload = json.loads(req.data.decode("utf-8"))
        res = MagicMock()
        res.__enter__.return_value = res
        res.read.return_value = json.dumps({"data": {"me": None}}).encode("utf-8")
        return res

    with patch("urllib.request.OpenerDirector.open", side_effect=mock_open_impl):
        api.get_user_profile()

    query_str = captured_payload.get("query", "")
    assert "karma" not in query_str
    assert "notificationUnreadCount" not in query_str
    assert "unreadConversationsCount" not in query_str


def test_get_user_profile_not_logged_in_returns_empty(api: PepperAPI) -> None:
    """Test get_user_profile returns empty dict when 'me' query returns null."""
    api.xsrf_token = "dummy_token"
    graphql_response = {
        "data": {
            "me": None,
        }
    }
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        profile = api.get_user_profile()
        assert profile == {}


def test_search_deals_success(api: PepperAPI) -> None:
    """Test successful HTML scraping search fallback."""
    mock_html = """
    <html>
      <a class="cept-tt test-class" title="Sony PlayStation 5 Slim" href="https://www.mydealz.de/deals/ps5"></a>
      <a class="cept-tt test-class" title="Xbox Series X" href="https://www.mydealz.de/deals/xbox"></a>
    </html>
    """
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = mock_html.encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        results = api.search_deals("gaming")

        assert len(results) == 2
        assert results[0]["title"] == "Sony PlayStation 5 Slim"
        assert results[0]["url"] == "https://www.mydealz.de/deals/ps5"
        assert results[1]["title"] == "Xbox Series X"
        assert results[1]["url"] == "https://www.mydealz.de/deals/xbox"


def test_search_deals_network_error(api: PepperAPI) -> None:
    """Test search handles page requests errors."""
    with patch(
        "urllib.request.OpenerDirector.open", side_effect=Exception("Network down")
    ):
        with pytest.raises(ConnectionError, match="Search page request failed"):
            api.search_deals("rtx")


def test_groups_parsing_in_get_deals(api: PepperAPI) -> None:
    """Test that get_deals correctly extracts and prettifies groups from GraphQL response."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "threads": [
                {
                    "threadId": "123",
                    "title": "Test Deal",
                    "url": "http://test",
                    "price": 10.0,
                    "nextBestPrice": 20.0,
                    "temperature": 100.0,
                    "publishedAt": 1234567,
                    "createdAt": 1234567,
                    "pickedAt": 0,
                    "description": "desc",
                    "voucherCode": None,
                    "type": "Deal",
                    "status": "Activated",
                    "isExpired": False,
                    "expirable": False,
                    "commentCount": 5,
                    "shareCount": 2,
                    "mainImage": None,
                    "merchant": None,
                    "user": None,
                    "groups": [
                        {
                            "groupsPath": [
                                {
                                    "pageUrl": "https://www.mydealz.de/gruppe/telefon-internet"
                                },
                                {"pageUrl": "https://www.mydealz.de/gruppe/dsl-cable"},
                            ]
                        }
                    ],
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
        assert deals[0]["groups"] == ["Telefon Internet", "Dsl Cable"]
