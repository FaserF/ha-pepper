# Pepper Deal Platforms (for Home Assistant)

[![GitHub Release](https://img.shields.io/github/release/FaserF/ha-pepper.svg?style=flat-square)](https://github.com/FaserF/ha-pepper/releases)
[![Downloads (Current release)](https://img.shields.io/github/downloads/FaserF/ha-pepper/latest/pepper.zip?label=Downloads%20(Current%20release)&style=flat-square)](https://github.com/FaserF/ha-pepper/releases)
[![License](https://img.shields.io/github/license/FaserF/ha-pepper.svg?style=flat-square)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-custom-orange.svg?style=flat-square)](https://hacs.xyz)
[![Add to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=pepper)
[![CI Orchestrator](https://github.com/FaserF/ha-pepper/actions/workflows/ci-orchestrator.yml/badge.svg)](https://github.com/FaserF/ha-pepper/actions/workflows/ci-orchestrator.yml)

A powerful, robust Home Assistant integration for **Pepper Deal Platforms** (MyDealz, HotUKDeals, Chollometro, Dealabs, etc.). Monitor hot deals, track specific keywords, and receive fire-alerts directly on your smart home dashboard.

---

## 🧭 Quick Links

| | | | |
| :--- | :--- | :--- | :--- |
| [📖 Features](#-features) | [📦 Installation](#-installation) | [⚙️ Configuration](#️-configuration) | [🛠️ Options](#️-options-flow) |
| [🛡️ Anti-Ban Protections](#-anti-ban-protections) | [🎨 Dashboard Examples](#-dashboard-card-examples) | [🧑‍💻 Development](#-development) | [📄 License](#-license) |

---

## ✨ Features

- 🚀 **GraphQL Feed & Search Scraping:** Connects directly to Pepper's internal GraphQL endpoints for the deal feed, avoiding fragile HTML DOM parsing. Search capabilities (`pepper.search` action and dynamic search sensor) scrape the HTML search results page via regex.
- 🌍 **Multi-Platform Support:** The integration supports the shared GraphQL core Pepper platforms. Below is the compatibility list:

  | Platform | Domain | Status | Details / Reason |
  | :--- | :--- | :---: | :--- |
  | **MyDealz** (Germany) | `mydealz.de` | :white_check_mark: | Primary development platform. Tested & working. |
  | **HotUKDeals** (United Kingdom) | `hotukdeals.com` | :white_check_mark: | Verified & working. |
  | **Chollometro (Spain)** | `chollometro.com` | :white_check_mark: | Verified & working. |
  | **Dealabs** (France) | `dealabs.com` | :white_check_mark: | Verified & working. |
  | **Pepper.pl** (Poland) | `pepper.pl` | :white_check_mark: | Verified & working. |
  | **Preisjäger** (Austria) | `preisjaeger.at` | :white_check_mark: | Verified & working. |
  | **Pepper.it** (Italy) | :x: | Uses different CSRF/authentication stack. |
  | **Pepper.ru** (Russia) | :x: | Uses different cookie & session mechanisms. |
  | **Pelando** (Brazil) | :x: | Runs on a different non-GraphQL legacy engine. |
  | **Desidime** (India) | :x: | Runs on a different non-GraphQL legacy engine. |
  | **Pepper.nl** (Netherlands) | :x: | Platform shutdown (no valid DNS records). |

- 🔐 **Optional Authentication:**
  - Login optionally during setup to unlock personalized account sensors.
  - Automatic reauthentication flow if credentials change or expire.
  - Keeps session cookies persistent across polls.

---

## 📡 Sensors

### Shipped Sensors

| Sensor | Entity ID | State | Description |
| :--- | :--- | :--- | :--- |
| 🔥 **Top Deals** | `sensor.pepper_top_deals` | Title of #1 deal | Main deal feed sensor. Rich feed statistics and deal items are stored in attributes. |
| 🎁 **Freebies** | `sensor.pepper_freebies` | Title of top freebie | Lists all active gratis deals in attributes. |
| 📈 **Feed Deal Count** | `sensor.pepper_feed_deal_count` | Number of deals | Total deals currently in the retrieved feed. |
| 🕒 **Freshest Deal** | `sensor.pepper_freshest_deal` | Title of newest deal | The most recently published deal in the feed. |
| 🔔 **Keyword Alerts** | `sensor.pepper_keyword_alerts` | Matched deal count | Count of deals matching your configured keywords *(disabled by default)*. |
| 🎫 **Vouchers** | `sensor.pepper_vouchers` | Active voucher count | Active vouchers with voucher codes in attributes *(disabled by default)*. |
| 🔌 **API Status** | `sensor.pepper_api_status` | `connected` / `error` | Diagnostic connection status with latency and error attributes. |
| 🎯 **Smart Filter Deals** | `sensor.pepper_smart_filter_deals` | Matched deal count | Deals matching custom temperature, price, merchant, and keyword filters *(disabled by default)*. |
| 🔍 **Dynamic Search** | `sensor.pepper_dynamic_search` | Title of top result | Live deal results updated via `pepper.set_search_query` action *(disabled by default)*. |
| 📁 **Group Top Deals** | `sensor.pepper_<group>_top_deals` | Title of top group deal | Dynamic per configured category/group *(created when groups are configured)*. |
| 📊 **Group Deal Count** | `sensor.pepper_<group>_deal_count` | Group deal count | Total deals in the configured category/group *(created when groups are configured)*. |
| 👤 **User Account** | `sensor.pepper_user_account` | Username | Consolidated account details and statistics *(requires login, created automatically)*. |

### Top Deals Attributes (`sensor.pepper_top_deals`)

Feed-wide statistics are consolidated directly into `sensor.pepper_top_deals` attributes:

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `deals` | list[dict] | Up to 10 slimmed deal objects from the feed. |
| `deals_count` | int | Total number of deals in the feed. |
| `average_temperature` | float | Average heat score across all deals in the feed. |
| `average_price` | float | Average price of priced deals. |
| `average_saving_percent` | float | Average discount percentage compared to next best price. |
| `cheapest_deal` | dict | `{"title": str, "price": float}` of the lowest priced deal. |
| `hottest_deal` | dict | `{"title": str, "temperature": float}` of the highest temperature deal. |
| `hottest_rising_deal` | dict | `{"title": str, "temp_change": float}` of the fastest heating deal. |
| `top_merchant` | string | Merchant with the highest number of deals in the feed. |
| `top_submitter` | string | Username with the most posted deals in the feed. |
| `top_group` | string | Most frequent category in the feed. |
| `price_errors_count` | int | Count of active (non-expired) price error deals. |
| `freebie_count` | int | Total freebie deals in the feed. |
| `voucher_count` | int | Total voucher deals in the feed. |
| `discussion_count` | int | Total discussion threads in the feed. |
| `expired_deals_count` | int | Count of expired deals in the feed. |
| `expired_deals_percentage` | float | Percentage of deals in the feed that are expired. |
| `picked_deals_count` | int | Deals featured/picked by editors (`picked_at > 0`). |
| `deal_type_distribution` | dict | Counts per thread type (`Deal`, `Voucher`, `Freebie`, `Discussion`). |
| `sort_mode` | string | Configured sort mode (`hot` or `new`). |

### User Account Attributes (`sensor.pepper_user_account`)

When logged in, user profile attributes are consolidated on `sensor.pepper_user_account`:

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `user_id` | string | Pepper user ID. |
| `email` | string | Account email address. |
| `avatar_url` | string | URL of user avatar image. |
| `thread_count` | int | Total deals posted by user. |
| `comment_count` | int | Total comments posted by user. |
| `badge_count` | int | Number of profile badges. |
| `badges` | list | Badges awarded to user. |
| `account_age_days` | int | Age of account in days. |
| `created_at` | string | ISO timestamp of account creation. |

---

## 🚨 Binary Sensors

All binary sensors are **disabled by default**.

| Sensor | Entity ID | Turns ON when... |
| :--- | :--- | :--- |
| 🔥 **High Temperature Alert** | `binary_sensor.pepper_high_temperature_alert` | Any deal in the feed exceeds the configured temperature threshold. |
| 🔕 **Expired Keyword Deal** | `binary_sensor.pepper_expired_keyword_deal` | Any of your keyword-tracked deals has expired (`is_expired=true` or status ≠ Activated). |
| 🎁 **Freebie Available** | `binary_sensor.pepper_freebie_available` | Any freebies are currently in the feed. |
| 🎫 **Voucher Available** | `binary_sensor.pepper_voucher_available` | Any vouchers are currently in the feed. |
| 🆕 **New Deal Available** | `binary_sensor.pepper_new_deal_available` | Any deals were published in the last 60 minutes. |
| ⌛ **Expirable Deal Available** | `binary_sensor.pepper_expirable_deal_available` | Any active (non-expired) deal has an expiration date. |
| 🔔 **Keyword Match Available** | `binary_sensor.pepper_keyword_match_available` | Any active (non-expired) deal matches the configured keywords. |
| 🌶️ **Super Hot Deal Available** | `binary_sensor.pepper_super_hot_deal_available` | Any deal temperature in the feed exceeds 500°. |
| ⚠️ **Price Error Available** | `binary_sensor.pepper_price_error_available` | Any active (non-expired) price error deal is in the feed. |
| 🎯 **Smart Filter Match** | `binary_sensor.pepper_smart_filter_match` | Any active deal matches all custom configured smart filter rules. |

---

## 📋 Deal Object Attributes

Deal arrays in sensor and binary sensor attributes use a lightweight structure capped at 10 items to prevent state size bloat:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Unique thread/deal ID |
| `title` | string | Deal title |
| `url` | string | Link to the deal page |
| `price` | float | Current deal price |
| `next_best_price` | float | Historical best price (for comparison) |
| `temperature` | float | Community heat/vote score |
| `published_at` | int | Unix timestamp of publication |
| `picked_at` | int | Unix timestamp when featured by editors (0 = not featured) |
| `voucher_code` | string | Coupon / voucher code (if applicable) |
| `type` | string | `Deal`, `Voucher`, `Freebie`, or `Discussion` |
| `status` | string | `Activated`, `Expired`, `Draft`, etc. |
| `is_expired` | bool | `true` if the deal is expired |
| `comment_count` | int | Number of comments |
| `share_count` | int | Number of shares |
| `merchant` | string | Merchant display name |
| `merchant_page_url` | string | URL to merchant profile on platform |
| `submitter` | string | Username of deal author |
| `image_url` | string | Deal image URL (CDN resolved) |
| `groups` | list[string] | Deal categories |
| `temp_change` | float | Temperature change since last poll |

---

## 🛠️ Services (Actions)

The integration registers actions to programmatically interact:

### `pepper.search`
Search for deals on the selected platform using HTML search scraping.

**Service Data:**
- `query` (string, required): The keyword to search for (e.g. `rtx 5080`).

**Response Data:**
- `deals`: A list of matching deals, each containing `title` and `url`.

### `pepper.refresh`
Force the integration to immediately pull the latest data from the platform.

### `pepper.set_search_query`
Update the search query string for the dynamic search sensor (`sensor.pepper_dynamic_search`) to track live search results on your dashboard.

**Service Data:**
- `query` (string, optional): The query to run for the dynamic search sensor (e.g. `rtx 4080`). Leave blank to clear.

---

## ⚙️ Configuration

Adding the Pepper platform is done entirely in the UI.

1. Navigate to **Settings > Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for **Pepper**.
3. Set the configuration:
   - **Platform:** Choose your local Pepper platform site (e.g. `mydealz.de`).
   - **Sort Mode:** Sort deals by `hot` (votes/temperature) or `new`.
   - **Scan Interval:** Minutes to wait between updates (default: `30` minutes).
   - **Keywords:** (Optional) Comma-separated list of keywords to track.
   - **Deal Groups:** (Optional) Comma-separated list of categories/groups to create dedicated sensors for.
   - **Temperature Threshold:** (Optional) Min heat to trigger the High Temp binary sensor (default: `500`).
   - **Max Deals to Fetch:** (Optional) Limit the number of deals fetched per update (default: `10`).
   - **Username:** (Optional) Your Pepper account username/email.
   - **Password:** (Optional) Your Pepper account password.
   - **Smart Filter Options:** (Optional) Set minimum temperature, maximum price, merchant filters, and keywords.

---

## 📦 Installation

### HACS (Recommended)

This integration is fully compatible with [HACS](https://hacs.xyz/).

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=FaserF&repository=ha-pepper&category=integration)

1. Open HACS in Home Assistant.
2. Click **Integrations** and select the three dots in the top-right corner.
3. Select **Custom repositories**.
4. Add the URL of the repository: `https://github.com/FaserF/ha-pepper` and select **Integration** as category.
5. Click **Add** and download/install the integration.
6. Restart Home Assistant.

### Manual Installation

1. Download the latest release `.zip` file from the [Releases page](https://github.com/FaserF/ha-pepper/releases).
2. Extract the `custom_components/pepper` directory into your Home Assistant's `config/custom_components/` directory.
3. Restart Home Assistant.

---

## 🛡️ Anti-Ban Protections

To prevent rate-limiting and session blocks by Cloudflare WAF or Pepper's server security, the integration implements a multi-layer anti-ban strategy:
1. **User-Agent Rotation:** Mimics authentic user sessions by rotating actual modern browser User-Agents.
2. **Accept Signatures:** Sends matching headers (`Sec-CH-UA`, `Sec-Fetch-Site`, etc.) matching the generated User-Agent signature.
3. **Random Jitter Delay:** Every background coordinator poll is delayed by a random offset of `2.0` to `6.0` seconds to evade periodic profiling detection.
4. **XSRF Validation:** Extracts valid cookies and validation tokens dynamically from the home page.
5. **Session Persistence:** Session cookies are retained across polls — the login is only performed once per session start, not on every update.

---

## 🎨 Dashboard Card Examples

### 1. Markdown Card listing top deals
A native Markdown card that loops through the deals attribute list and outputs them in a clean format:

```yaml
type: markdown
title: "🔥 Top MyDealz Deals"
content: >
  {% if state_attr('sensor.pepper_top_deals', 'deals') %}
    | Temp | Deal | Price | Händler | Typ |
    | :--- | :--- | :--- | :--- | :--- |
    {% for deal in state_attr('sensor.pepper_top_deals', 'deals')[:10] %}
      | **{{ deal.temperature | int }}°** | [{{ deal.title }}]({{ deal.url }}) | {% if deal.price %}{{ deal.price }}€{% else %}-{% endif %} | *{{ deal.merchant }}* | {{ deal.type }} |
    {% endfor %}
  {% else %}
    Keine Deals geladen.
  {% endif %}
```

### 2. Automation: Alert when tracked deal expires

```yaml
alias: "Alert when tracked deal expires"
trigger:
  - platform: state
    entity_id: binary_sensor.pepper_expired_keyword_deal
    to: "on"
action:
  - service: notify.mobile_app
    data:
      title: "⚠️ Deal abgelaufen!"
      message: "Ein von dir verfolgter Deal ist abgelaufen."
```

### 3. Automation: Notify on very hot new deal

```yaml
alias: "Alert on fire deal"
trigger:
  - platform: state
    entity_id: binary_sensor.pepper_high_temperature_alert
    to: "on"
action:
  - service: notify.mobile_app
    data:
      title: "🔥 Feuer-Deal!"
      message: >
        {{ state_attr('sensor.pepper_top_deals', 'deals') | selectattr('temperature', '>=', 500) | map(attribute='title') | first }}
```

---

## 📖 API Documentation

For in-depth details on the private GraphQL endpoints, query schemas, variables, static image CDN patterns, and anti-ban mechanics, refer to the [Pepper Group API Documentation](docs/pepper_api.md).

---

## 🛡️ Support This Project

> I maintain this integration in my **free time alongside my regular job** — bug hunting, testing on multiple platforms, and refining configurations.
>
> **This project is and will always remain 100% free.**
>
> Donations are completely voluntary — but every bit of support helps! 💪

<div align="center">

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor%20on-GitHub-%23EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/FaserF)&nbsp;&nbsp;
[![PayPal](https://img.shields.io/badge/Donate%20via-PayPal-%2300457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/FaserF)

</div>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
