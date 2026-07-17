"""Constants for the Pepper integration."""

DOMAIN = "pepper"

CONF_SORT_MODE = "sort_mode"
CONF_LIMIT = "limit"
CONF_PLATFORM = "platform"
CONF_KEYWORDS = "keywords"
CONF_TEMP_THRESHOLD = "temp_threshold"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_GROUPS = "groups"


DEFAULT_SORT_MODE = "hot"
DEFAULT_LIMIT = 10
DEFAULT_SCAN_INTERVAL = 30  # Minutes
DEFAULT_PLATFORM = "mydealz.de"
DEFAULT_TEMP_THRESHOLD = 500

# Verified working Pepper platforms sharing the core GraphQL stack
PLATFORMS_MAP = {
    "mydealz.de": "MyDealz (Germany)",
    "hotukdeals.com": "HotUKDeals (United Kingdom)",
    "chollometro.com": "Chollometro (Spain)",
    "dealabs.com": "Dealabs (France)",
    "pepper.pl": "Pepper.pl (Poland)",
    "preisjaeger.at": "Preisjäger (Austria)",
}
