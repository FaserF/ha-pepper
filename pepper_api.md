# Pepper Group Undocumented GraphQL API Documentation

This document describes the findings and implementation details of the private, undocumented GraphQL API used across the **Pepper Group** deal sharing platforms (including MyDealz.de, HotUKDeals.com, Chollometro.com, Dealabs.com, Pepper.pl, and Preisjaeger.at).

---

## 🌍 Supported Platforms & Endpoints

All verified Pepper platforms share the same core GraphQL architecture, but run on localized domains and static CDN hosts:

| Platform | Core Domain | GraphQL Endpoint | Static CDN Host |
| :--- | :--- | :--- | :--- |
| **MyDealz** (Germany) | `mydealz.de` | `https://www.mydealz.de/graphql` | `https://static.mydealz.de` |
| **HotUKDeals** (United Kingdom) | `hotukdeals.com` | `https://www.hotukdeals.com/graphql` | `https://static.hotukdeals.com` |
| **Chollometro** (Spain) | `chollometro.com` | `https://www.chollometro.com/graphql` | `https://static.chollometro.com` |
| **Dealabs** (France) | `dealabs.com` | `https://www.dealabs.com/graphql` | `https://static.dealabs.com` |
| **Pepper.pl** (Poland) | `pepper.pl` | `https://www.pepper.pl/graphql` | `https://static.pepper.pl` |
| **Preisjäger** (Austria) | `preisjaeger.at` | `https://www.preisjaeger.at/graphql` | `https://static.preisjaeger.at` |

---

## 🛡️ Authentication & CSRF Bypass (Anti-Teapot Flow)

Direct POST requests to localized `/graphql` endpoints without a session are protected by Cloudflare WAF and return `HTTP 418 I'm a teapot` with error message `{"message":"Whiiiiiiieeee","data":[]}`.

To bypass this check:
1. **Initialize Session:** Perform a GET request to the homepage `https://www.{domain}/`.
2. **Extract Cookies:** Save the cookies returned in the response, notably `xsrf_t` and `pepper_session`.
3. **Add Headers:** For all subsequent POST requests to `/graphql`:
   - Send the cookies in the `Cookie` header.
   - Send the extracted `xsrf_t` token in the `X-Xsrf-Token` header.
   - Send `X-Requested-With: XMLHttpRequest` header.
   - Mimic a real browser user agent and headers (without compression headers like `gzip` to avoid raw compressed binary payloads in standard urllib).

---

## 📊 GraphQL Schema & Queries

### 1. Fetching Daily Hottest Deals (`hottestWidget`)

To get the actual "Hottest Deals of the Day" (the popular highlights shown on the main page/sidebar), query the `hottestWidget` field.

#### Query Definition
```graphql
query HottestWidget($filter: ThreadFilter!) {
  hottestWidget(filter: $filter) {
    options {
      text
      value
    }
    selected {
      text
      value
    }
    threads {
      threadId
      title
      url
      price
      temperature
      publishedAt
      createdAt
      description
      merchant {
        merchantName
      }
      mainImage {
        path
        name
      }
    }
  }
}
```

#### Variables
An empty filter `{}` defaults to retrieving the hottest deals of the day:
```json
{
  "filter": {}
}
```

---

### 2. Fetching Chronological Deals (`threads`)

To retrieve deals chronologically (e.g. "Newest Deals" tab), use the standard `threads` query.

#### Query Definition
```graphql
query getThreads($filter: ThreadFilter!) {
  threads(filter: $filter) {
    threadId
    title
    url
    price
    temperature
    publishedAt
    createdAt
    description
    merchant {
      merchantName
    }
    mainImage {
      path
      name
    }
  }
}
```

#### Variables
Passing an empty filter returns the default newest deals:
```json
{
  "filter": {}
}
```

---

### 3. User Authentication (`login`)

Authentication is completed via the `login` GraphQL mutation, which updates the session cookies on the Pepper platform.

```graphql
mutation login($input: LoginInput!) {
  login(input: $input) {
    user {
      userId
      username
    }
  }
}
```

#### Variables
```json
{
  "input": {
    "identity": "<username>",
    "password": "<password>"
  }
}
```

---

### 4. Fetching Logged-in User Profile (`me`)

To retrieve the authenticated user's profile statistics and notifications, query the `me` field.

```graphql
query getMe {
  me {
    userId
    username
    karma
    notificationUnreadCount
    unreadConversationsCount
  }
}
```

---

### 5. Filtering Deals (Freebies, Vouchers & Coupon Codes)

The `ThreadFilter` input allows filtering the deals/threads feed:
- **Freebies (Gratis):** Pass `"isFreebies": true` in the filter variables.
- **Vouchers (Gutscheine):** Pass `"isVoucher": true` in the filter variables, and request the `couponCode` field to fetch active voucher/discount codes.

---

## 🖼️ Static Image CDN Resolution

Images are resolved dynamically using the `mainImage` subfields. The image URL is constructed as:
```
{cdn_host}/{path}/{name}/re/300x300/qt/60/{name}.jpg
```
Where `re/300x300/qt/60` is the default thumbnail cropping and compression profile used by the platforms.

---

## 🚫 Anti-Ban & Rate-Limit Strategies

To prevent IP bans or rate limits by the Pepper group firewalls:
1. **User-Agent Rotation:** Randomize browser headers on every session initialization.
2. **Session Persistence:** Retain session cookies (`xsrf_t` and `pepper_session`) across updates rather than re-logging on every call.
3. **Shared Updates (Coordinator):** Fetch all deal types inside a single Home Assistant DataUpdateCoordinator call rather than requesting data individually per entity.
4. **Timeouts:** Restrict all API requests to a `10s` timeout to prevent blocking worker threads in Home Assistant.
