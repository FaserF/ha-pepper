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
- 🎁 **Freebies Sensor (`sensor.pepper_freebies`):**
  - Monitor free items / gratis deals.
  - State = title of the top freebie.
  - Attributes = list of active freebies.
- 🎫 **Vouchers Sensor (`sensor.pepper_vouchers`):**
  - Monitor active voucher codes (e.g. for coupon codes).
  - State = count of active vouchers.
  - Attributes = list of vouchers with `coupon_code` field.
  - *Disabled by default.*
- 👤 **Personalized User Sensors:**
  - **User Karma (`sensor.pepper_user_karma`):** Tracks your contribution points.
  - **User Notifications (`sensor.pepper_user_notifications`):** Unread alarm/reply count.
  - **User Conversations (`sensor.pepper_user_conversations`):** Unread inbox messages count.
  - *Only created if credentials are provided. Disabled by default.*
- 🔔 **Keyword Alert Sensor (`sensor.pepper_keyword_alerts`):**
  - Monitor custom keywords (e.g., `playstation, switch, rtx`).
  - State = count of matching active deals.
  - Attributes = list of matching deal items.
  - *Disabled by default.*
- 🔥 **High Temperature Alert (`binary_sensor.pepper_high_temperature_alert`):**
  - Switches to `on` if any deal crosses a voter temperature limit (e.g. `500°`).
  - *Disabled by default.*
- ⚡ **Shared Updates:** All sensors fetch and process data in a single combined network call to keep API overhead at a minimum.

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
   - **Username:** (Optional) Your Pepper account username/email.
   - **Password:** (Optional) Your Pepper account password.

---

## 🛠️ Services (Actions)

The integration registers a service/action to programmatically search for deals:

### `pepper.search`
Search for deals on the selected platform. This returns the list of matching deals.

**Service Data:**
- `query` (string, required): The keyword to search for (e.g. `rtx 5080`).

**Response Data:**
- `deals`: A list of matching deals, each containing `title` and `url`.

---

## 🛡️ Anti-Ban Protections

To prevent rate-limiting and session blocks by Cloudflare WAF or Pepper's server security, the integration implements a multi-layer anti-ban strategy:
1. **User-Agent Rotation:** Mimics authentic user sessions by rotating actual modern browser User-Agents.
2. **Accept Signatures:** Sends matching headers (`Sec-CH-UA`, `Sec-Fetch-Site`, etc.) matching the generated User-Agent signature.
3. **Random Jitter Delay:** Every background coordinator poll is delayed by a random offset of `1.0` to `5.0` seconds to evade periodic profiling detection.
4. **XSRF Validation:** Extracts valid cookies and validation tokens dynamically from the home page.

---

## 🎨 Dashboard Card Examples

### 1. Markdown Card listing top deals
A native Markdown card that loops through the deals attribute list and outputs them in a clean format:

```yaml
type: markdown
title: "🔥 Top MyDealz Deals"
content: >
  {% if state_attr('sensor.pepper_top_deals', 'deals') %}
    | Temp | Deal | Price | Händler |
    | :--- | :--- | :--- | :--- |
    {% for deal in state_attr('sensor.pepper_top_deals', 'deals')[:10] %}
      | **{{ deal.temperature | int }}°** | [{{ deal.title }}]({{ deal.url }}) | {% if deal.price %}{{ deal.price }}€{% else %}-{% endif %} | *{{ deal.merchant }}* |
    {% endfor %}
  {% else %}
    Keine Deals geladen.
  {% endif %}
```

---

## 📖 API Documentation

For in-depth details on the private GraphQL endpoints, query schemas, variables, static image CDN patterns, and anti-ban mechanics, refer to the [Pepper Group API Documentation](pepper_api.md).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
