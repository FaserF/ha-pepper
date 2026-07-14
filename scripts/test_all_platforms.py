# ruff: noqa: E402
"""Script to live test all Pepper platforms and API features."""

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

import os

# Add custom_components directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.pepper.const import PLATFORMS_MAP
from custom_components.pepper.pepper_api import PepperAPI


def test_platform(domain, name):
    print(f"\nTesting platform: {name} ({domain})...")
    api = PepperAPI(platform=domain)

    try:
        print("1. Fetching session...")
        api.fetch_session()
        print(f"   Success! XSRF Token: {api.xsrf_token}")
    except Exception as e:
        print(f"   Failed to fetch session: {e}")
        return False

    for sort in ["hot", "new"]:
        try:
            print(f"2. Fetching {sort} deals...")
            deals = api.get_deals(sort_mode=sort)
            print(f"   Success! Fetched {len(deals)} deals.")
            if deals:
                deal = deals[0]
                print(
                    f"   Sample Deal: {deal['title']} | Temp: {deal['temperature']}° | Price: {deal['price']}"
                )
                if deal["image_url"]:
                    print(f"   Image CDN URL: {deal['image_url']}")
        except Exception as e:
            print(f"   Failed to fetch {sort} deals: {e}")
            return False

    return True


if __name__ == "__main__":
    print("Starting Pepper Platform Live Tests...")
    success = True
    for domain, name in PLATFORMS_MAP.items():
        # Test mydealz.de first and a few others to verify
        res = test_platform(domain, name)
        if not res:
            success = False

    if success:
        print("\nAll Pepper platforms and public features tested successfully!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)
