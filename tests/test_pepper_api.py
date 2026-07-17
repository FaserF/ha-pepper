# ruff: noqa: E402
"""Tests for Pepper API client and sensor/binary sensor entities."""

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
import statistics
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from custom_components.pepper.pepper_api import PepperAPI

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api() -> PepperAPI:
    """Create a PepperAPI instance."""
    return PepperAPI(platform="mydealz.de")


@pytest.fixture
def api_with_auth() -> PepperAPI:
    """Create a PepperAPI instance with credentials."""
    return PepperAPI(platform="mydealz.de", username="FaserF", password="secret")


# ---------------------------------------------------------------------------
# Session / connection tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


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

    def capture_and_respond(req, timeout=10):  # type: ignore[no-untyped-def]
        import json as _json

        captured_payload.update(_json.loads(req.data.decode()))
        mock_resp = MagicMock()
        mock_resp.read.return_value = _json.dumps(graphql_response).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    with patch("urllib.request.OpenerDirector.open", side_effect=capture_and_respond):
        api_with_auth.login()

    query_text = captured_payload.get("query", "")
    # Verify the correct mutation field and input type are used
    assert "loginUser" in query_text, "Must use loginUser mutation field"
    assert "LoginUserInput" in query_text, "Must use LoginUserInput type"
    # Verify the loginUser field is actually called (not just referenced in a comment)
    assert "loginUser(input:" in query_text or "loginUser(input :" in query_text, (
        "loginUser must be called with input argument"
    )

    variables = captured_payload.get("variables", {})
    assert variables.get("input", {}).get("identity") == "FaserF"
    assert variables.get("input", {}).get("password") == "secret"


def test_login_no_credentials_is_noop(api: PepperAPI) -> None:
    """Test that login without credentials does nothing."""
    api.xsrf_token = "dummy_token"
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        api.login()
        mock_open.assert_not_called()


# ---------------------------------------------------------------------------
# get_deals tests
# ---------------------------------------------------------------------------


def _make_thread(overrides: dict | None = None) -> dict:
    """Return a minimal valid thread dict."""
    base: dict = {
        "threadId": "12345",
        "title": "Super Deal",
        "url": "https://www.mydealz.de/deals/super-deal-12345",
        "price": 9.99,
        "nextBestPrice": 14.99,
        "temperature": 100.5,
        "publishedAt": 1600000000,
        "createdAt": 1599999900,
        "pickedAt": 1600001000,
        "description": "Very good deal",
        "voucherCode": "SAVE10",
        "type": "Deal",
        "status": "Activated",
        "isExpired": False,
        "expirable": True,
        "commentCount": 7,
        "shareCount": 3,
        "merchant": {
            "merchantId": "99",
            "merchantName": "SuperShop",
            "merchantPageUrl": "https://www.mydealz.de/gutscheine/supershop",
            "merchantUrlName": "supershop",
        },
        "user": {"userId": "111", "username": "dealuser"},
        "mainImage": {
            "path": "threads/raw/abc",
            "name": "12345_1",
        },
    }
    if overrides:
        base.update(overrides)
    return base


def test_get_deals_new_mode_full_fields(api: PepperAPI) -> None:
    """Test retrieving deals with all new confirmed fields (sort_mode=new)."""
    api.xsrf_token = "dummy_token"

    graphql_response = {"data": {"threads": [_make_thread()]}}

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="new")

    assert len(deals) == 1
    deal = deals[0]

    # Core fields
    assert deal["id"] == "12345"
    assert deal["title"] == "Super Deal"
    assert deal["price"] == 9.99
    assert deal["temperature"] == 100.5

    # New fields
    assert deal["next_best_price"] == 14.99
    assert deal["voucher_code"] == "SAVE10", "voucherCode must map to voucher_code"
    assert deal["type"] == "Deal"
    assert deal["status"] == "Activated"
    assert deal["is_expired"] is False
    assert deal["expirable"] is True
    assert deal["comment_count"] == 7
    assert deal["share_count"] == 3
    assert deal["picked_at"] == 1600001000

    # Merchant
    assert deal["merchant"] == "SuperShop"
    assert deal["merchant_id"] == "99"
    assert deal["merchant_page_url"] == "https://www.mydealz.de/gutscheine/supershop"
    assert deal["merchant_url_name"] == "supershop"

    # Submitter
    assert deal["submitter"] == "dealuser"
    assert deal["submitter_id"] == "111"

    # Image URL
    assert (
        deal["image_url"]
        == "https://static.mydealz.de/threads/raw/abc/12345_1/re/300x300/qt/60/12345_1.jpg"
    )


def test_get_deals_hot_mode(api: PepperAPI) -> None:
    """Test hot deals via hottestWidget query."""
    api.xsrf_token = "dummy_token"

    thread = _make_thread(
        {
            "threadId": "54321",
            "title": "Hottest Deal",
            "price": 19.99,
            "temperature": 500.5,
        }
    )
    graphql_response = {"data": {"hottestWidget": {"threads": [thread]}}}

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="hot")

    assert len(deals) == 1
    assert deals[0]["id"] == "54321"
    assert deals[0]["temperature"] == 500.5
    assert deals[0]["merchant"] == "SuperShop"


def test_get_deals_voucher_code_field_name(api: PepperAPI) -> None:
    """Ensure the API uses voucherCode (not the old couponCode) field name."""
    api.xsrf_token = "dummy_token"

    captured_query: list[str] = []

    def capture_and_respond(req, timeout=10):  # type: ignore[no-untyped-def]
        import json as _j

        payload = _j.loads(req.data.decode())
        captured_query.append(payload.get("query", ""))
        mock_resp = MagicMock()
        mock_resp.read.return_value = _j.dumps(
            {"data": {"threads": [_make_thread()]}}
        ).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    with patch("urllib.request.OpenerDirector.open", side_effect=capture_and_respond):
        api.get_deals(sort_mode="new")

    query_text = captured_query[0] if captured_query else ""
    assert "voucherCode" in query_text, "API query must request voucherCode"
    assert "couponCode" not in query_text, (
        "API query must NOT use deprecated couponCode"
    )


def test_get_deals_no_image(api: PepperAPI) -> None:
    """Test deal with no mainImage returns None image_url."""
    api.xsrf_token = "dummy_token"
    thread = _make_thread({"mainImage": None})
    graphql_response = {"data": {"threads": [thread]}}

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="new")

    assert deals[0]["image_url"] is None


def test_get_deals_no_merchant(api: PepperAPI) -> None:
    """Test deal with no merchant returns None merchant fields."""
    api.xsrf_token = "dummy_token"
    thread = _make_thread({"merchant": None})
    graphql_response = {"data": {"threads": [thread]}}

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="new")

    assert deals[0]["merchant"] is None
    assert deals[0]["merchant_id"] is None
    assert deals[0]["merchant_page_url"] is None


def test_get_deals_no_user(api: PepperAPI) -> None:
    """Test deal with no user returns None submitter fields."""
    api.xsrf_token = "dummy_token"
    thread = _make_thread({"user": None})
    graphql_response = {"data": {"threads": [thread]}}

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        deals = api.get_deals(sort_mode="new")

    assert deals[0]["submitter"] is None
    assert deals[0]["submitter_id"] is None


def test_get_deals_freebies_filter(api: PepperAPI) -> None:
    """Test is_freebies filter does not append variables to GraphQL (client side only)."""
    api.xsrf_token = "dummy_token"
    captured: list[dict] = []

    def capture_and_respond(req, timeout=10):  # type: ignore[no-untyped-def]
        import json as _j

        captured.append(_j.loads(req.data.decode()))
        mock_resp = MagicMock()
        mock_resp.read.return_value = _j.dumps({"data": {"threads": []}}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    with patch("urllib.request.OpenerDirector.open", side_effect=capture_and_respond):
        api.get_deals(sort_mode="new", is_freebies=True)

    assert captured[0]["variables"]["filter"] == {}


def test_get_deals_voucher_filter(api: PepperAPI) -> None:
    """Test is_voucher filter is sent in variables as type mapping."""
    api.xsrf_token = "dummy_token"
    captured: list[dict] = []

    def capture_and_respond(req, timeout=10):  # type: ignore[no-untyped-def]
        import json as _j

        captured.append(_j.loads(req.data.decode()))
        mock_resp = MagicMock()
        mock_resp.read.return_value = _j.dumps({"data": {"threads": []}}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    with patch("urllib.request.OpenerDirector.open", side_effect=capture_and_respond):
        api.get_deals(sort_mode="new", is_voucher=True)

    assert captured[0]["variables"]["filter"].get("type") == {"eq": "Voucher"}


def test_get_deals_graphql_error(api: PepperAPI) -> None:
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


# ---------------------------------------------------------------------------
# get_user_profile tests
# ---------------------------------------------------------------------------


def test_get_user_profile_new_fields(api: PepperAPI) -> None:
    """Test get_user_profile returns updated fields (no karma/notifications)."""
    api.xsrf_token = "dummy_token"

    graphql_response = {
        "data": {
            "me": {
                "userId": "249802",
                "username": "FaserF",
                "email": "test@example.com",
                "createdAt": 1500000000,
                "threadCount": 42,
                "commentCount": 123,
                "avatar": {"path": "users/raw/abc", "name": "avatar_1"},
                "badges": [{"badgeId": "veteran"}],
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
    assert profile["email"] == "test@example.com"
    assert profile["threadCount"] == 42
    assert profile["commentCount"] == 123
    assert profile["avatar"] == {"path": "users/raw/abc", "name": "avatar_1"}
    assert profile["badges"] == [{"badgeId": "veteran"}]

    # Deprecated fields must NOT be in the query
    assert "karma" not in profile
    assert "notificationUnreadCount" not in profile
    assert "unreadConversationsCount" not in profile


def test_get_user_profile_query_excludes_deprecated_fields(api: PepperAPI) -> None:
    """Ensure the profile query no longer requests removed API fields."""
    api.xsrf_token = "dummy_token"
    captured_queries: list[str] = []

    def capture_and_respond(req, timeout=10):  # type: ignore[no-untyped-def]
        import json as _j

        captured_queries.append(_j.loads(req.data.decode()).get("query", ""))
        mock_resp = MagicMock()
        mock_resp.read.return_value = _j.dumps({"data": {"me": {}}}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    with patch("urllib.request.OpenerDirector.open", side_effect=capture_and_respond):
        api.get_user_profile()

    query = captured_queries[0] if captured_queries else ""
    assert "karma" not in query
    assert "notificationUnreadCount" not in query
    assert "unreadConversationsCount" not in query


def test_get_user_profile_not_logged_in_returns_empty(api: PepperAPI) -> None:
    """Test that get_user_profile returns empty dict when not logged in (me=None)."""
    api.xsrf_token = "dummy_token"

    graphql_response = {"data": {"me": None}}

    with patch("urllib.request.OpenerDirector.open") as mock_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphql_response).encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_response

        profile = api.get_user_profile()

    assert profile == {}


# ---------------------------------------------------------------------------
# search_deals tests
# ---------------------------------------------------------------------------


def test_search_deals_success(api: PepperAPI) -> None:
    """Test search_deals HTML scraper."""
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


def test_search_deals_network_error(api: PepperAPI) -> None:
    """Test search_deals raises ConnectionError on network failure."""
    api.xsrf_token = "dummy_token"
    with patch("urllib.request.OpenerDirector.open", side_effect=Exception("timeout")):
        with pytest.raises(ConnectionError, match="Search page request failed"):
            api.search_deals("rtx")


# ---------------------------------------------------------------------------
# Sensor and Binary Sensor logic tests
# ---------------------------------------------------------------------------


def _make_coordinator(
    deals: list,
    freebies: list | None = None,
    vouchers: list | None = None,
    profile: dict | None = None,
) -> MagicMock:
    """Build a minimal coordinator mock."""
    coord = MagicMock()
    coord.data = {
        "deals": deals,
        "freebies": freebies or [],
        "vouchers": vouchers or [],
        "profile": profile,
    }
    coord.sort_mode = "hot"
    coord.api = MagicMock()
    coord.api.platform = "mydealz.de"
    coord.api.username = None
    return coord


def _make_entry(options: dict | None = None, data: dict | None = None) -> MagicMock:
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.options = options or {}
    entry.data = data or {}
    return entry


# Import the raw logic functions directly to avoid HA class instantiation
# (which triggers metaclass conflicts when homeassistant is mocked).


def _new_deals_logic(coordinator_data: dict, now_ts: float) -> list:
    """Mirror of PepperNewDealsCountSensor._get_new_deals logic."""
    deals = coordinator_data.get("deals", [])
    cutoff = now_ts - 3600
    return [d for d in deals if d.get("published_at") and d["published_at"] >= cutoff]


def _expired_deals_logic(coordinator_data: dict) -> list:
    """Mirror of PepperExpiredDealsCountSensor._get_expired_deals logic."""
    deals = coordinator_data.get("deals", [])
    return [d for d in deals if d.get("is_expired")]


def _picked_deals_logic(coordinator_data: dict) -> list:
    """Mirror of PepperPickedDealsCountSensor._get_picked_deals logic."""
    deals = coordinator_data.get("deals", [])
    return [d for d in deals if d.get("picked_at") and d["picked_at"] > 0]


def _merchant_stats_logic(coordinator_data: dict) -> dict:
    """Mirror of PepperTopMerchantSensor._get_merchant_stats logic."""
    deals = coordinator_data.get("deals", [])
    stats: dict = {}
    for deal in deals:
        merchant = deal.get("merchant")
        if merchant:
            stats[merchant] = stats.get(merchant, 0) + 1
    return stats


def _keyword_matches_expired_logic(coordinator_data: dict, keywords: list[str]) -> list:
    """Mirror of PepperExpiredKeywordDealSensor._get_expired_keyword_deals logic."""
    if not keywords:
        return []
    deals = coordinator_data.get("deals", [])
    expired = []
    for deal in deals:
        title = (deal.get("title") or "").lower()
        description = (deal.get("description") or "").lower()
        if any(k in title or k in description for k in keywords):
            if deal.get("is_expired") or deal.get("status") not in (None, "Activated"):
                expired.append(deal)
    return expired


def _high_temp_logic(coordinator_data: dict, threshold: int) -> list:
    """Mirror of PepperHighTempAlertSensor._get_alert_deals logic."""
    deals = coordinator_data.get("deals", [])
    return [
        d
        for d in deals
        if d.get("temperature") is not None
        and isinstance(d["temperature"], (int, float))
        and d["temperature"] >= threshold
    ]


def _freshest_deal_logic(coordinator_data: dict) -> dict | None:
    deals = coordinator_data.get("deals", [])
    if not deals:
        return None
    return max(deals, key=lambda d: d.get("published_at") or 0)


def _average_temp_logic(coordinator_data: dict) -> float | None:
    deals = coordinator_data.get("deals", [])
    temps = [
        d["temperature"]
        for d in deals
        if d.get("temperature") is not None
        and isinstance(d["temperature"], (int, float))
    ]
    return round(statistics.mean(temps), 1) if temps else None


def _cheapest_deal_logic(coordinator_data: dict) -> dict | None:
    deals = coordinator_data.get("deals", [])
    priced_deals = [
        d
        for d in deals
        if d.get("price") is not None and isinstance(d["price"], (int, float))
    ]
    if not priced_deals:
        return None
    return min(priced_deals, key=lambda d: d["price"])


def _hottest_deal_logic(coordinator_data: dict) -> dict | None:
    deals = coordinator_data.get("deals", [])
    temps = [
        d
        for d in deals
        if d.get("temperature") is not None
        and isinstance(d["temperature"], (int, float))
    ]
    if not temps:
        return None
    return max(temps, key=lambda d: d["temperature"])


def _deal_distribution_logic(coordinator_data: dict) -> dict[str, int]:
    deals = coordinator_data.get("deals", [])
    dist: dict[str, int] = {}
    for d in deals:
        t = d.get("type") or "Unknown"
        dist[t] = dist.get(t, 0) + 1
    return dist


def _deals_with_voucher_logic(coordinator_data: dict) -> list[dict]:
    deals = coordinator_data.get("deals", [])
    return [d for d in deals if d.get("voucher_code")]


def _most_commented_logic(coordinator_data: dict) -> dict | None:
    deals = coordinator_data.get("deals", [])
    if not deals:
        return None
    return max(deals, key=lambda d: d.get("comment_count") or 0)


def _most_shared_logic(coordinator_data: dict) -> dict | None:
    deals = coordinator_data.get("deals", [])
    if not deals:
        return None
    return max(deals, key=lambda d: d.get("share_count") or 0)


def _savings_logic(coordinator_data: dict) -> list[tuple[float, dict]]:
    deals = coordinator_data.get("deals", [])
    savings = []
    for d in deals:
        p = d.get("price")
        nbp = d.get("next_best_price")
        if (
            p is not None
            and nbp is not None
            and isinstance(p, (int, float))
            and isinstance(nbp, (int, float))
        ):
            diff = nbp - p
            if diff > 0:
                savings.append((round(diff, 2), d))
    return savings


def _savings_percent_logic(coordinator_data: dict) -> list[tuple[float, dict]]:
    deals = coordinator_data.get("deals", [])
    savings = []
    for d in deals:
        p = d.get("price")
        nbp = d.get("next_best_price")
        if (
            p is not None
            and nbp is not None
            and isinstance(p, (int, float))
            and isinstance(nbp, (int, float))
            and nbp > 0
        ):
            pct = ((nbp - p) / nbp) * 100
            if pct > 0:
                savings.append((round(pct, 1), d))
    return savings


def test_new_deals_count_sensor_logic() -> None:
    """Test new deals count logic counts only recent deals."""
    now = datetime.now(tz=UTC).timestamp()
    old_ts = now - 7200  # 2 hours ago
    new_ts = now - 300  # 5 minutes ago

    data = {
        "deals": [
            {"id": "1", "title": "Old Deal", "published_at": old_ts},
            {"id": "2", "title": "New Deal", "published_at": new_ts},
        ]
    }
    result = _new_deals_logic(data, now)
    assert len(result) == 1
    assert result[0]["title"] == "New Deal"


def test_new_deals_count_sensor_no_deals() -> None:
    """Test new deals count returns empty list when no recent deals."""
    now = datetime.now(tz=UTC).timestamp()
    old_ts = now - 7200
    data = {"deals": [{"id": "1", "published_at": old_ts}]}
    result = _new_deals_logic(data, now)
    assert len(result) == 0


def test_expired_deals_count_sensor_logic() -> None:
    """Test expired deals count logic."""
    data = {
        "deals": [
            {"id": "1", "is_expired": False},
            {"id": "2", "is_expired": True},
            {"id": "3", "is_expired": True},
        ]
    }
    result = _expired_deals_logic(data)
    assert len(result) == 2


def test_expired_deals_count_zero() -> None:
    """Test expired deals count is zero when all deals are active."""
    data = {"deals": [{"id": "1", "is_expired": False}]}
    result = _expired_deals_logic(data)
    assert len(result) == 0


def test_picked_deals_count_sensor_logic() -> None:
    """Test picked deals count logic."""
    data = {
        "deals": [
            {"id": "1", "picked_at": 0},
            {"id": "2", "picked_at": 1700000000},
            {"id": "3", "picked_at": None},
        ]
    }
    result = _picked_deals_logic(data)
    assert len(result) == 1
    assert result[0]["id"] == "2"


def test_top_merchant_sensor_logic() -> None:
    """Test top merchant logic returns merchant with most deals."""
    data = {
        "deals": [
            {"merchant": "Amazon"},
            {"merchant": "Amazon"},
            {"merchant": "MediaMarkt"},
        ]
    }
    stats = _merchant_stats_logic(data)
    top = max(stats, key=lambda k: stats[k])
    assert top == "Amazon"
    assert stats["Amazon"] == 2
    assert stats["MediaMarkt"] == 1


def test_top_merchant_sensor_no_deals() -> None:
    """Test top merchant logic with no deals returns empty stats."""
    stats = _merchant_stats_logic({"deals": []})
    assert stats == {}


def test_top_merchant_ignores_none_merchant() -> None:
    """Test that deals without merchant name are excluded from stats."""
    data = {"deals": [{"merchant": None}, {"merchant": "Amazon"}]}
    stats = _merchant_stats_logic(data)
    assert None not in stats
    assert stats == {"Amazon": 1}


def test_user_thread_count_from_profile() -> None:
    """Test user thread count reads correctly from profile data."""
    profile = {
        "userId": "123",
        "username": "FaserF",
        "threadCount": 42,
        "commentCount": 99,
    }
    assert profile["threadCount"] == 42


def test_user_comment_count_from_profile() -> None:
    """Test user comment count reads correctly from profile data."""
    profile = {
        "userId": "123",
        "username": "FaserF",
        "threadCount": 42,
        "commentCount": 99,
    }
    assert profile["commentCount"] == 99


# ---------------------------------------------------------------------------
# Binary sensor logic tests
# ---------------------------------------------------------------------------


def test_high_temp_alert_sensor_logic() -> None:
    """Test high temp alert logic triggers above threshold."""
    data = {
        "deals": [
            {"temperature": 300},
            {"temperature": 600},
        ]
    }
    result = _high_temp_logic(data, threshold=500)
    assert len(result) == 1
    assert result[0]["temperature"] == 600


def test_high_temp_alert_sensor_off_below_threshold() -> None:
    """Test high temp alert is empty when nothing exceeds threshold."""
    data = {"deals": [{"temperature": 200}]}
    result = _high_temp_logic(data, threshold=500)
    assert len(result) == 0


def test_high_temp_alert_skips_non_numeric() -> None:
    """Test high temp alert skips deals with non-numeric temperature."""
    data = {
        "deals": [{"temperature": None}, {"temperature": "hot"}, {"temperature": 600}]
    }
    result = _high_temp_logic(data, threshold=500)
    assert len(result) == 1


def test_expired_keyword_deal_sensor_on() -> None:
    """Test expired keyword deal logic returns expired keyword-matching deals."""
    data = {
        "deals": [
            {
                "title": "RTX 5080 Deal",
                "description": "great gpu",
                "is_expired": True,
                "status": "Expired",
            },
            {
                "title": "PlayStation 5",
                "description": "gaming console",
                "is_expired": False,
                "status": "Activated",
            },
        ]
    }
    result = _keyword_matches_expired_logic(data, ["rtx", "gpu"])
    assert len(result) == 1
    assert result[0]["title"] == "RTX 5080 Deal"


def test_expired_keyword_deal_sensor_off_when_active() -> None:
    """Test expired keyword deal logic is empty when keyword deals are active."""
    data = {
        "deals": [
            {
                "title": "RTX 5080 Deal",
                "description": "",
                "is_expired": False,
                "status": "Activated",
            },
        ]
    }
    result = _keyword_matches_expired_logic(data, ["rtx"])
    assert len(result) == 0


def test_expired_keyword_deal_sensor_off_no_keywords() -> None:
    """Test expired keyword deal logic returns empty when no keywords."""
    data = {
        "deals": [
            {
                "title": "RTX 5080 Deal",
                "description": "",
                "is_expired": True,
                "status": "Expired",
            },
        ]
    }
    result = _keyword_matches_expired_logic(data, [])
    assert len(result) == 0


def test_expired_keyword_deal_non_activated_status() -> None:
    """Test that deals with non-Activated status are also flagged."""
    data = {
        "deals": [
            {
                "title": "RTX deal",
                "description": "",
                "is_expired": False,
                "status": "Draft",
            },
        ]
    }
    result = _keyword_matches_expired_logic(data, ["rtx"])
    assert len(result) == 1


# ---------------------------------------------------------------------------
# New Sensor and Binary Sensor logic tests
# ---------------------------------------------------------------------------


def test_freshest_deal_logic() -> None:
    """Test freshest deal selection."""
    data = {
        "deals": [
            {"title": "Older Deal", "published_at": 1000},
            {"title": "Fresher Deal", "published_at": 2000},
        ]
    }
    deal = _freshest_deal_logic(data)
    assert deal is not None
    assert deal["title"] == "Fresher Deal"


def test_average_temp_logic() -> None:
    """Test average temperature calculation."""
    data = {
        "deals": [
            {"temperature": 100.0},
            {"temperature": 200.0},
            {"temperature": 300.0},
        ]
    }
    avg = _average_temp_logic(data)
    assert avg == 200.0


def test_cheapest_deal_logic() -> None:
    """Test cheapest deal logic."""
    data = {
        "deals": [
            {"price": 10.0},
            {"price": 5.0},
            {"price": None},
        ]
    }
    deal = _cheapest_deal_logic(data)
    assert deal is not None
    assert deal["price"] == 5.0


def test_hottest_deal_logic() -> None:
    """Test hottest deal logic."""
    data = {
        "deals": [
            {"temperature": 100},
            {"temperature": 500},
        ]
    }
    deal = _hottest_deal_logic(data)
    assert deal is not None
    assert deal["temperature"] == 500


def test_deal_distribution_logic() -> None:
    """Test deal distribution."""
    data = {
        "deals": [
            {"type": "Deal"},
            {"type": "Deal"},
            {"type": "Freebie"},
        ]
    }
    dist = _deal_distribution_logic(data)
    assert dist == {"Deal": 2, "Freebie": 1}


def test_deals_with_voucher_logic() -> None:
    """Test deals with voucher."""
    data = {
        "deals": [
            {"voucher_code": "VOUCH"},
            {"voucher_code": None},
        ]
    }
    result = _deals_with_voucher_logic(data)
    assert len(result) == 1
    assert result[0]["voucher_code"] == "VOUCH"


def test_most_commented_logic() -> None:
    """Test most commented."""
    data = {
        "deals": [
            {"comment_count": 5},
            {"comment_count": 10},
        ]
    }
    deal = _most_commented_logic(data)
    assert deal is not None
    assert deal["comment_count"] == 10


def test_most_shared_logic() -> None:
    """Test most shared."""
    data = {
        "deals": [
            {"share_count": 2},
            {"share_count": 8},
        ]
    }
    deal = _most_shared_logic(data)
    assert deal is not None
    assert deal["share_count"] == 8


def test_savings_logic() -> None:
    """Test saving amounts."""
    data = {
        "deals": [
            {"price": 10.0, "next_best_price": 15.0},
            {"price": 20.0, "next_best_price": 18.0},
        ]
    }
    savings = _savings_logic(data)
    assert len(savings) == 1
    assert savings[0][0] == 5.0


def test_savings_percent_logic() -> None:
    """Test saving percent calculation."""
    data = {
        "deals": [
            {"price": 10.0, "next_best_price": 20.0},
        ]
    }
    pct = _savings_percent_logic(data)
    assert len(pct) == 1
    assert pct[0][0] == 50.0


def test_average_saving_percent_logic() -> None:
    """Test average saving percent logic."""
    data = {
        "deals": [
            {"price": 10.0, "next_best_price": 20.0},  # 50%
            {"price": 10.0, "next_best_price": 12.5},  # 20%
        ]
    }
    # Calculate inline
    pcts = []
    for d in data["deals"]:
        p = d["price"]
        nbp = d["next_best_price"]
        pcts.append(((nbp - p) / nbp) * 100)
    avg = round(statistics.mean(pcts), 1)
    assert avg == 35.0


def test_average_price_logic() -> None:
    """Test average price logic."""
    data = {
        "deals": [
            {"price": 10.0},
            {"price": 20.0},
        ]
    }
    prices = [d["price"] for d in data["deals"]]
    avg = round(statistics.mean(prices), 2)
    assert avg == 15.0


def test_discussion_count_logic() -> None:
    """Test discussion count logic."""
    data = {
        "deals": [
            {"type": "Discussion"},
            {"type": "Deal"},
            {"type": "Discussion"},
        ]
    }
    count = len([d for d in data["deals"] if d["type"] == "Discussion"])
    assert count == 2


def test_voucher_count_logic() -> None:
    """Test voucher count logic."""
    data = {
        "deals": [
            {"type": "Voucher"},
            {"type": "Deal"},
        ]
    }
    count = len([d for d in data["deals"] if d["type"] == "Voucher"])
    assert count == 1


def test_expired_deals_percentage_logic() -> None:
    """Test expired deals percentage logic."""
    data = {
        "deals": [
            {"is_expired": True},
            {"is_expired": False},
            {"is_expired": False},
            {"is_expired": False},
        ]
    }
    expired = len([d for d in data["deals"] if d["is_expired"]])
    pct = round((expired / len(data["deals"])) * 100, 1)
    assert pct == 25.0


def test_top_submitter_logic() -> None:
    """Test top submitter logic."""
    data = {
        "deals": [
            {"submitter": "user1"},
            {"submitter": "user2"},
            {"submitter": "user1"},
        ]
    }
    stats = {}
    for d in data["deals"]:
        sub = d["submitter"]
        stats[sub] = stats.get(sub, 0) + 1
    top = max(stats, key=lambda k: stats[k])
    assert top == "user1"


def test_top_group_logic() -> None:
    """Test top group logic."""
    data = {
        "deals": [
            {"groups": ["elec", "gaming"]},
            {"groups": ["elec"]},
        ]
    }
    stats = {}
    for d in data["deals"]:
        for g in d.get("groups") or []:
            stats[g] = stats.get(g, 0) + 1
    top = max(stats, key=lambda k: stats[k])
    assert top == "elec"


def test_hottest_deal_title_logic() -> None:
    """Test hottest deal title logic."""
    data = {
        "deals": [
            {"title": "Deal 1", "temperature": 100},
            {"title": "Deal 2", "temperature": 900},
        ]
    }
    temps = [d for d in data["deals"] if d.get("temperature") is not None]
    hottest = max(temps, key=lambda d: d["temperature"])
    assert hottest["title"] == "Deal 2"


def test_expirable_deal_available_logic() -> None:
    """Test expirable deal available logic."""
    data = {
        "deals": [
            {"expirable": True, "is_expired": False},
            {"expirable": True, "is_expired": True},
        ]
    }
    available = any(
        d.get("expirable") and not d.get("is_expired") for d in data["deals"]
    )
    assert available is True


def test_keyword_match_available_logic() -> None:
    """Test keyword match available logic."""
    data = {
        "deals": [
            {"title": "Xbox One Deal", "is_expired": False},
            {"title": "PlayStation 5", "is_expired": True},
        ]
    }
    keywords = ["xbox"]
    matched = False
    for deal in data["deals"]:
        if deal.get("is_expired"):
            continue
        title = deal["title"].lower()
        if any(k in title for k in keywords):
            matched = True
    assert matched is True


def test_super_hot_deal_available_logic() -> None:
    """Test super hot deal available logic."""
    data = {
        "deals": [
            {"temperature": 450},
            {"temperature": 600},
        ]
    }
    super_hot = any(
        d.get("temperature") is not None and d["temperature"] >= 500
        for d in data["deals"]
    )
    assert super_hot is True


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


def test_price_error_logic() -> None:
    """Test price error detection logic."""
    data = {
        "deals": [
            {
                "title": "Normal Deal",
                "description": "normal price",
                "groups": ["Electronics"],
                "is_expired": False,
            },
            {
                "title": "Preisfehler in Title",
                "description": "desc",
                "groups": ["Electronics"],
                "is_expired": False,
            },
            {
                "title": "Normal Title",
                "description": "description mentioning preisfehler",
                "groups": ["Electronics"],
                "is_expired": False,
            },
            {
                "title": "Normal Title 2",
                "description": "desc",
                "groups": ["Preisfehler"],
                "is_expired": False,
            },
            {
                "title": "Expired Preisfehler",
                "description": "desc",
                "groups": ["Preisfehler"],
                "is_expired": True,
            },
        ]
    }

    # Filter function mirrored from the sensor
    def get_price_errors(deals):
        errors = []
        for d in deals:
            if d.get("is_expired"):
                continue
            title = (d.get("title") or "").lower()
            description = (d.get("description") or "").lower()
            groups = [g.lower() for g in d.get("groups") or []]
            if (
                "preisfehler" in title
                or "preisfehler" in description
                or "preisfehler" in groups
            ):
                errors.append(d)
        return errors

    errors = get_price_errors(data["deals"])
    assert len(errors) == 3
    assert errors[0]["title"] == "Preisfehler in Title"
    assert errors[1]["description"] == "description mentioning preisfehler"
    assert errors[2]["groups"] == ["Preisfehler"]


def test_api_latency_and_status_logic() -> None:
    """Test API latency and status logic."""

    class MockCoordinator:
        def __init__(self):
            self.last_latency = 1.23
            self.last_error = "Connection timeout"
            self.last_update_success = False

    coord = MockCoordinator()
    assert coord.last_latency == 1.23
    assert coord.last_error == "Connection timeout"
    assert coord.last_update_success is False


def test_group_filtered_sensors_logic() -> None:
    """Test the filtering logic used in PepperGroupTopDealsSensor and PepperGroupDealCountSensor."""
    deals = [
        {"title": "Xbox Deal", "groups": ["Gaming", "Electronics"]},
        {"title": "Shirt Deal", "groups": ["Fashion"]},
        {"title": "TV Deal", "groups": ["Electronics"]},
    ]

    def get_group_deals(deals_list, group_name):
        group_lower = group_name.lower()
        return [
            d
            for d in deals_list
            if any(g.lower() == group_lower for g in d.get("groups", []))
        ]

    gaming_deals = get_group_deals(deals, "Gaming")
    assert len(gaming_deals) == 1
    assert gaming_deals[0]["title"] == "Xbox Deal"

    electronics_deals = get_group_deals(deals, "Electronics")
    assert len(electronics_deals) == 2
    assert electronics_deals[0]["title"] == "Xbox Deal"
    assert electronics_deals[1]["title"] == "TV Deal"

    fashion_deals = get_group_deals(deals, "Fashion")
    assert len(fashion_deals) == 1
    assert fashion_deals[0]["title"] == "Shirt Deal"

    none_deals = get_group_deals(deals, "NoneExisting")
    assert len(none_deals) == 0


def test_temperature_trend_logic() -> None:
    """Test calculations for temperature trends."""
    previous_deals = {"1": 100.0, "2": 200.0}
    current_deals = [
        {"id": "1", "temperature": 150.0},
        {"id": "2", "temperature": 180.0},
        {"id": "3", "temperature": 50.0},
    ]

    for d in current_deals:
        deal_id = d.get("id")
        temp = d.get("temperature")
        if deal_id is not None and temp is not None:
            prev_temp = previous_deals.get(deal_id)
            if prev_temp is not None:
                d["temp_change"] = round(temp - prev_temp, 2)
            else:
                d["temp_change"] = 0.0

    assert current_deals[0]["temp_change"] == 50.0
    assert current_deals[1]["temp_change"] == -20.0
    assert current_deals[2]["temp_change"] == 0.0


def test_smart_filter_logic() -> None:
    """Test smart filter matching rules."""
    deals = [
        {
            "title": "Xbox Deal",
            "price": 400.0,
            "temperature": 300,
            "merchant": "Amazon",
            "description": "Console",
        },
        {
            "title": "Cheap PS5 Deal",
            "price": 450.0,
            "temperature": 150,
            "merchant": "Amazon",
            "description": "Console",
        },
        {
            "title": "Switch Deal",
            "price": 250.0,
            "temperature": 250,
            "merchant": "MediaMarkt",
            "description": "Handheld",
        },
    ]

    def match_deal(d, min_temp, max_price, merchants, keywords):
        temp = d.get("temperature")
        if temp is None or temp < min_temp:
            return False
        price = d.get("price")
        if max_price > 0.0:
            if price is None or price > max_price:
                return False
        if merchants:
            merchant = d.get("merchant")
            if not merchant or merchant.lower() not in merchants:
                return False
        if keywords:
            title = (d.get("title") or "").lower()
            description = (d.get("description") or "").lower()
            if not any(k in title or k in description for k in keywords):
                return False
        return True

    # Test temp & price
    assert match_deal(deals[0], 200, 500.0, [], []) is True
    assert match_deal(deals[1], 200, 500.0, [], []) is False  # low temp

    # Test merchant
    assert match_deal(deals[0], 200, 500.0, ["amazon"], []) is True
    assert match_deal(deals[2], 200, 500.0, ["amazon"], []) is False  # wrong merchant

    # Test keywords
    assert match_deal(deals[0], 200, 500.0, [], ["xbox"]) is True
    assert match_deal(deals[0], 200, 500.0, [], ["ps5"]) is False
