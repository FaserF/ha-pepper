# Pepper for Home Assistant

This integration brings deal data from **Pepper Group platforms** (such as MyDealz.de, HotUKDeals.com, Chollometro.com, Dealabs.com, Pepper.pl, and Preisjaeger.at) into your Home Assistant instance, allowing you to track prices, temperatures, and new deals to trigger automations.

## Features
- **Top Deals Sensor**: Shows the title of the top deal as state, and a full list of recent deals (including price, heat/temperature, links, merchant name, and image URLs) in attributes.
- **Freebies Sensor**: Shows the top active freebie and lists all current gratis deals.
- **Vouchers Sensor**: Tracks the count of active coupon vouchers (disabled by default).
- **Personalized User Sensors**: Track Karma, Notifications, and Conversations counts when logged in (disabled by default).
- **Search Service/Action**: Programmatically search deals using `pepper.search` returning results directly.
- **Undocumented API Integration**: Connects via GraphQL directly to the internal API (no fragile HTML scraping).
- **Config Flow Setup**: Configure directly in the UI.

## Getting Started
- See [Installation](installation.md) and [Configuration](configuration.md) to set it up.
- For technical details about the undocumented API, see the [Pepper GraphQL API Documentation](pepper_api.md).
