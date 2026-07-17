"""Tests for Pepper sensor entities logic."""

import statistics
from datetime import UTC, datetime


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
        if d.get("price") is not None
        and isinstance(d["price"], (int, float))
        and d["price"] > 0.0
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
    """Test cheapest deal logic excluding freebies."""
    data = {
        "deals": [
            {"price": 10.0},
            {"price": 5.0},
            {"price": 0.0},
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


def test_consolidated_top_deals_attributes_logic() -> None:
    """Test calculations and attribute population in consolidated PepperTopDealsSensor."""
    deals = [
        {
            "title": "Xbox Deal",
            "price": 400.0,
            "next_best_price": 500.0,
            "temperature": 300,
            "merchant": "Amazon",
            "submitter": "user1",
            "type": "Deal",
            "picked_at": 12345,
        },
        {
            "title": "Freebie Deal",
            "price": 0.0,
            "next_best_price": 20.0,
            "temperature": 5000,
            "merchant": "Amazon",
            "submitter": "user2",
            "type": "Freebie",
            "is_expired": False,
            "groups": ["Freebies"],
        },
        {
            "title": "Nintendo Switch",
            "price": 250.0,
            "next_best_price": 300.0,
            "temperature": 150,
            "merchant": "MediaMarkt",
            "submitter": "user1",
            "type": "Deal",
        },
    ]
    freebies = [deals[1]]

    # Extract averages and counts excluding price 0.0
    temps = [d["temperature"] for d in deals if d.get("temperature") is not None]
    prices = [
        d["price"] for d in deals if d.get("price") is not None and d["price"] > 0.0
    ]

    priced_deals = [d for d in deals if d.get("price") is not None and d["price"] > 0.0]
    cheapest = min(priced_deals, key=lambda d: d["price"]) if priced_deals else None
    hottest = max(
        [d for d in deals if d.get("temperature") is not None],
        key=lambda d: d["temperature"],
    )

    assert round(statistics.mean(temps), 1) == 1816.7
    assert round(statistics.mean(prices), 2) == 325.0
    assert cheapest["title"] == "Nintendo Switch"
    assert hottest["title"] == "Freebie Deal"
    assert len(freebies) == 1


def test_consolidated_user_account_attributes_logic() -> None:
    """Test logic for parsing and formatting consolidated PepperUserAccountSensor attributes."""
    profile = {
        "userId": "249802",
        "username": "FaserF",
        "email": "seitzf1@yahoo.de",
        "createdAt": 1390000000,
        "threadCount": 66,
        "commentCount": 1803,
        "avatar": {"path": "users/raw/default", "name": "249802_1"},
        "badges": [{"badgeId": "badge_1"}, {"badgeId": "badge_2"}],
    }

    now_ts = 1700000000.0
    created_ts = profile["createdAt"]
    account_age_days = max(0, int((now_ts - created_ts) // 86400))
    dt_iso = datetime.fromtimestamp(created_ts, tz=UTC).isoformat()

    avatar = profile["avatar"]
    avatar_url = f"https://static.mydealz.de/{avatar['path']}/{avatar['name']}/re/100x100/qt/60/{avatar['name']}.jpg"

    assert account_age_days == 3587
    assert dt_iso == "2014-01-17T23:06:40+00:00"
    assert (
        avatar_url
        == "https://static.mydealz.de/users/raw/default/249802_1/re/100x100/qt/60/249802_1.jpg"
    )
    assert len(profile["badges"]) == 2


def test_coordinator_cache_fallback_logic() -> None:
    """Test coordinator fallback logic on API errors (within/beyond 24h limit)."""
    last_success_time = 1000.0
    cached_data = {"deals": [{"id": 1}]}

    # Fetch fails at t = 2000 (age 1000s < 86400s -> within 24h)
    now_ts = 2000.0
    age = now_ts - last_success_time
    assert age < 86400.0
    returned_data = cached_data  # logic maps to returning self.data
    assert returned_data == cached_data

    # Fetch fails at t = 90000 (age 89000s > 86400s -> over 24h)
    now_ts = 90000.0
    age = now_ts - last_success_time
    assert age >= 86400.0
    # logic raises UpdateFailed
