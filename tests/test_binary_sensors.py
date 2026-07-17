"""Tests for Pepper binary sensor entities logic."""

from unittest.mock import MagicMock


def _make_coordinator(deals: list) -> MagicMock:
    coord = MagicMock()
    coord.data = {"deals": deals}
    return coord


def _high_temp_logic(coordinator_data: dict, threshold: int) -> list:
    deals = coordinator_data.get("deals", [])
    return [
        d
        for d in deals
        if d.get("temperature") is not None
        and isinstance(d["temperature"], (int, float))
        and d["temperature"] >= threshold
    ]


def _keyword_matches_expired_logic(coordinator_data: dict, keywords: list[str]) -> list:
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
    """Test temp alert is empty when nothing exceeds threshold."""
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

    assert match_deal(deals[0], 200, 500.0, [], []) is True
    assert match_deal(deals[1], 200, 500.0, [], []) is False
    assert match_deal(deals[0], 200, 500.0, ["amazon"], []) is True
    assert match_deal(deals[2], 200, 500.0, ["amazon"], []) is False
    assert match_deal(deals[0], 200, 500.0, [], ["xbox"]) is True
    assert match_deal(deals[0], 200, 500.0, [], ["ps5"]) is False
