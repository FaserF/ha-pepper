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

- 🚀 **Zero Scraping:** Connects directly to the Pepper internal GraphQL endpoints, avoiding fragile HTML DOM parsing.
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
  - Login optionally during setup to unlock personalized sensors.
  - Keeps session cookies persistent across polls.

---

## 📡 Sensors

### Always Enabled

| Sensor | Entity ID | Description |
| :--- | :--- | :--- |
| 🔥 **Top Deals** | `sensor.pepper_top_deals` | State = title of the #1 deal. Attributes = full list of deals with all fields. |
| 🎁 **Freebies** | `sensor.pepper_freebies` | State = title of the top freebie. Attributes = list of free items. |
| 📈 **Feed Deal Count** | `sensor.pepper_feed_deal_count` | Total deals currently in the retrieved feed. |
| 🕒 **Freshest Deal** | `sensor.pepper_freshest_deal` | State = title of the most recently published deal. |

### Disabled by Default (enable as needed)

| Sensor | Entity ID | Description |
| :--- | :--- | :--- |
| 🔔 **Keyword Alerts** | `sensor.pepper_keyword_alerts` | Count of deals matching your configured keywords. |
| 🎫 **Vouchers** | `sensor.pepper_vouchers` | Count of active vouchers with `voucher_code` in attributes. |
| 🆕 **New Deals (Last Hour)** | `sensor.pepper_new_deals_last_hour` | Count of deals published within the last 60 minutes. |
| ⌛ **Expired Deals** | `sensor.pepper_expired_deals` | Count of expired deals currently in the feed. |
| ⭐ **Picked Deals** | `sensor.pepper_picked_deals` | Count of deals that have been featured/picked by editors (`pickedAt > 0`). |
| 🏪 **Top Merchant** | `sensor.pepper_top_merchant` | Merchant name with the most deals in the current feed. Attributes = full ranking. |
| 🌡️ **Average Temperature** | `sensor.pepper_average_temperature` | Average temperature of the retrieved deals. Attrs: min, max, median, std dev. |
| 🪙 **Cheapest Deal** | `sensor.pepper_cheapest_deal` | Price of the cheapest priced deal. |
| 🌶️ **Hottest Deal Temp** | `sensor.pepper_hottest_deal_temperature` | Temperature of the single hottest deal. |
| 📊 **Deal Distribution** | `sensor.pepper_deal_type_distribution` | Most common deal type (Deal/Voucher/Freebie/Discussion). Attrs: type counts. |
| 🎫 **Deals with Voucher** | `sensor.pepper_deals_with_voucher_count` | Count of deals in the main feed having a voucher code. |
| 🎁 **Freebie Count** | `sensor.pepper_freebie_count` | Integer count of freebies. |
| 💬 **Most Commented Deal** | `sensor.pepper_most_commented_deal` | Title of the deal with the most comments. |
| 🔗 **Most Shared Deal** | `sensor.pepper_most_shared_deal` | Title of the deal with the most shares. |
| 💸 **Best Saving (Absolute)** | `sensor.pepper_best_saving_absolute` | Highest absolute saving (next_best_price - price). |
| 🏷️ **Best Saving (Percent)** | `sensor.pepper_best_saving_percent` | Highest percentage saving. |

### User Sensors *(requires login, disabled by default)*

| Sensor | Entity ID | Description |
| :--- | :--- | :--- |
| 📝 **User Thread Count** | `sensor.pepper_user_thread_count` | Total number of deal threads the logged-in user has posted. |
| 💬 **User Comment Count** | `sensor.pepper_user_comment_count` | Total number of comments the logged-in user has posted. |
| 📅 **User Account Age (Days)** | `sensor.pepper_user_account_age_days` | Number of days since the user's account was created. |
| 🏆 **User Badge Count** | `sensor.pepper_user_badge_count` | Number of badges earned by the user. |

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

---

## 📋 Deal Attributes

Every deal object in sensor attributes includes the following fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Unique thread/deal ID |
| `title` | string | Deal title |
| `url` | string | Link to the deal page |
| `shareable_link` | string | Short shareable URL |
| `price` | float | Current deal price |
| `next_best_price` | float | Historical best price (for price comparison) |
| `temperature` | float | Community heat/vote score |
| `published_at` | int | Unix timestamp of publication |
| `created_at` | int | Unix timestamp of creation |
| `picked_at` | int | Unix timestamp when featured by editors (0 = not featured) |
| `description` | string | Full deal description |
| `voucher_code` | string | Coupon / voucher code (if applicable) |
| `type` | string | `Deal`, `Voucher`, `Freebie`, or `Discussion` |
| `status` | string | `Activated`, `Expired`, `Draft`, etc. |
| `is_expired` | bool | `true` if the deal is expired |
| `expirable` | bool | `true` if the deal has an expiry date |
| `comment_count` | int | Number of comments |
| `share_count` | int | Number of shares |
| `merchant` | string | Merchant/store display name |
| `merchant_id` | string | Internal merchant ID |
| `merchant_page_url` | string | URL to the merchant's page on the platform |
| `merchant_url_name` | string | Merchant URL slug |
| `submitter` | string | Username of the deal submitter |
| `submitter_id` | string | User ID of the deal submitter |
| `image_url` | string | Deal image URL (CDN resolved) |

---

## 🛠️ Services (Actions)

The integration registers actions to programmatically interact:

### `pepper.search`
Search for deals on the selected platform. This returns the list of matching deals.

**Service Data:**
- `query` (string, required): The keyword to search for (e.g. `rtx 5080`).

**Response Data:**
- `deals`: A list of matching deals, each containing `title` and `url`.

### `pepper.refresh`
Force the integration to immediately pull the latest data from the platform.

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
   - **Temperature Threshold:** (Optional) Min heat to trigger the High Temp binary sensor (default: `500`).
   - **Max Deals to Fetch:** (Optional) Limit the number of deals fetched per update (default: `30`).
   - **Username:** (Optional) Your Pepper account username/email.
   - **Password:** (Optional) Your Pepper account password.

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
3. **Random Jitter Delay:** Every background coordinator poll is delayed by a random offset of `1.0` to `5.0` seconds to evade periodic profiling detection.
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

For in-depth details on the private GraphQL endpoints, query schemas, variables, static image CDN patterns, and anti-ban mechanics, refer to the [Pepper Group API Documentation](pepper_api.md).

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
