# Pepper Group Undocumented GraphQL API Documentation

This document describes the findings and implementation details of the private, undocumented GraphQL API used across the **Pepper Group** deal sharing platforms (including MyDealz.de, HotUKDeals.com, Chollometro.com, Dealabs.com, Pepper.pl, and Preisjaeger.at).

> **Note on Discovery Method:** All field availability data in this document was verified empirically via live API probing (field-by-field testing) against `mydealz.de`. GraphQL introspection (`__type` queries) is blocked by the Cloudflare WAF with HTTP 418. Only fields with confirmed responses are documented here.

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
   - Send the cookies in the `Cookie` header (managed automatically via `http.cookiejar`).
   - Send the extracted `xsrf_t` token in the `X-Xsrf-Token` header.
   - Send `X-Requested-With: XMLHttpRequest` header.
   - Mimic a real browser user agent and headers (without compression headers like `gzip` to avoid raw compressed binary payloads in standard urllib).
   - Include `Sec-Fetch-*` headers consistent with a CORS XHR request (`Sec-Fetch-Dest: empty`, `Sec-Fetch-Mode: cors`, `Sec-Fetch-Site: same-origin`).

### ⚠️ Rate Limiting & Session Invalidation

- The WAF enforces **aggressive rate limits** — too many consecutive GraphQL requests within a short window re-trigger the 418 block, even with a valid session.
- After ~5–8 rapid queries, the session gets "teapot blocked". Adding `time.sleep(1–2)` between queries helps.
- **GraphQL introspection (`__type` queries) is blocked outright** — the WAF returns 418 immediately for any introspection query regardless of session state.
- The session **does not persist** across process restarts (cookies are in-memory). A new GET to the homepage is required on each startup.

---

## 📊 GraphQL Schema & Queries

### 1. Fetching Daily Hottest Deals (`hottestWidget`)

To get the actual "Hottest Deals of the Day" (the popular highlights shown on the main page/sidebar), query the `hottestWidget` field.

#### Query Definition
```graphql
query HottestWidget($filter: ThreadFilter!) {
  hottestWidget(filter: $filter) {
    threads {
      threadId
      title
      url
      shareableLink
      price
      nextBestPrice
      temperature
      publishedAt
      createdAt
      pickedAt
      description
      voucherCode
      type
      status
      isExpired
      expirable
      commentCount
      shareCount
      mainImage {
        path
        name
      }
      merchant {
        merchantId
        merchantName
        merchantPageUrl
        merchantUrlName
      }
      user {
        userId
        username
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
    shareableLink
    price
    nextBestPrice
    temperature
    publishedAt
    createdAt
    pickedAt
    description
    voucherCode
    type
    status
    isExpired
    expirable
    commentCount
    shareCount
    mainImage {
      path
      name
    }
    merchant {
      merchantId
      merchantName
      merchantPageUrl
      merchantUrlName
    }
    user {
      userId
      username
    }
    groups {
      groupsPath
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

### 3. Thread Type (`Thread`) — Confirmed Fields

All fields below were confirmed to exist on the `Thread` type via live API probing:

| Field | Type | Notes |
| :--- | :--- | :--- |
| `threadId` | String | Unique deal/thread identifier |
| `title` | String | Deal title |
| `url` | String | Direct link to deal page |
| `shareableLink` | String | Short/shareable link (may be null) |
| `price` | Float | Current deal price (null if freebie or voucher only) |
| `nextBestPrice` | Float | Historical best price for comparison (may be null) |
| `temperature` | Float | Community heat score (can be negative) |
| `publishedAt` | Int | Unix timestamp of publication |
| `createdAt` | Int | Unix timestamp of creation |
| `pickedAt` | Int | Unix timestamp when deal was featured/picked (0 if not picked) |
| `description` | String | Full deal description (HTML) |
| `voucherCode` | String | **Correct field name** — coupon/voucher code (was wrongly called `couponCode` in old docs) |
| `type` | String | Deal type: `"Deal"`, `"Voucher"`, `"Freebie"`, `"Discussion"` |
| `status` | String | Deal status: `"Activated"`, `"Expired"`, `"Draft"`, etc. |
| `isExpired` | Boolean | True if the deal is expired |
| `expirable` | Boolean | True if the deal has an expiry date |
| `commentCount` | Int | Number of comments on the deal |
| `shareCount` | Int | Number of times shared |
| `mainImage.path` | String | CDN path segment for image (see Image URL Resolution) |
| `mainImage.name` | String | CDN filename segment for image |
| `merchant.merchantId` | String | Unique merchant identifier |
| `merchant.merchantName` | String | Display name of the merchant/store |
| `merchant.merchantPageUrl` | String | Full URL to merchant's page on the platform |
| `merchant.merchantUrlName` | String | Merchant's URL slug |
| `user.userId` | String | Deal submitter's user ID |
| `user.username` | String | Deal submitter's username |
| `groups.groupsPath` | String | Path of the group this deal belongs to (may be empty list) |

#### ❌ Fields Confirmed NOT Available on Thread

| Field | Error |
| :--- | :--- |
| `couponCode` | Use `voucherCode` instead |
| `expiredAt` | Does not exist; use `isExpired` + `expirable` |
| `voteCount` | Does not exist; use `temperature` |
| `shareLink` | Use `shareableLink` instead |
| `category` | Not a field on Thread type |
| `tags` | Not a field on Thread type |
| `group` (singular) | Use `groups` (plural) instead |

---

### 4. User Authentication (`loginUser`)

```graphql
mutation login($input: LoginUserInput!) {
  loginUser(input: $input) {
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
    "identity": "<username_or_email>",
    "password": "<password>"
  }
}
```

---

### 5. Fetching Logged-in User Profile (`me`)

To retrieve the authenticated user's profile statistics, query the `me` field. Note that several fields documented in older API research are **no longer available** (see table below).

```graphql
query getMe {
  me {
    userId
    username
    email
    createdAt
    threadCount
    commentCount
    avatar {
      path
      name
    }
    badges {
      badgeId
    }
  }
}
```

#### Confirmed `me` Fields

| Field | Type | Notes |
| :--- | :--- | :--- |
| `userId` | String | User's unique ID |
| `username` | String | Display name |
| `email` | String | Email address (only visible to own account) |
| `createdAt` | Int | Account creation Unix timestamp |
| `threadCount` | Int | Number of threads/deals submitted |
| `commentCount` | Int | Number of comments posted |
| `avatar.path` | String | CDN path for avatar image |
| `avatar.name` | String | CDN filename for avatar image |
| `badges.badgeId` | String | List of badge IDs awarded to user |

#### ❌ `me` Fields Confirmed NOT Available

| Field | Notes |
| :--- | :--- |
| `karma` | Removed from API (previously documented) |
| `notificationUnreadCount` | Removed from API (previously documented) |
| `unreadConversationsCount` | Removed from API (previously documented) |
| `followersCount` | Not available |
| `followingCount` | Not available |
| `lastLoginAt` | Not available |
| `isPro` | Not available |
| `roleSet` | Not available |

---

### 6. Filtering Deals (`ThreadFilter`)

The `ThreadFilter` input allows filtering the deals/threads feed. Confirmed working filter fields:

| Filter Field | Usage | Example |
| :--- | :--- | :--- |
| `isFreebies` | Boolean — filter to freebies only | `{"filter": {"isFreebies": true}}` |
| `isVoucher` | Boolean — filter to vouchers only | `{"filter": {"isVoucher": true}}` |

> **Note:** The `type` filter field exists (`ThreadTypeFilter` object type) but its exact sub-fields (`eq`, `in`, etc.) have not been confirmed as the WAF blocked testing after rate limit. The boolean filters `isFreebies` and `isVoucher` are the reliably confirmed approach.

---

### 7. User Notifications (`notifications`)

The `notifications` query exists and returns a `UserNotifications` object type. However, **the exact sub-fields of `UserNotifications` could not be confirmed** due to WAF rate limiting blocking queries after login. The field `notificationId` on `UserNotifications` was confirmed to not exist.

---

## 🖼️ Static Image CDN Resolution

Images are resolved dynamically using the `mainImage` subfields. The image URL is constructed as:
```
{cdn_host}/{path}/{name}/re/300x300/qt/60/{name}.jpg
```
Where `re/300x300/qt/60` is the default thumbnail cropping and compression profile used by the platforms.

**Example:**
- `path`: `threads/raw/abc`
- `name`: `12345_1`
- Result: `https://static.mydealz.de/threads/raw/abc/12345_1/re/300x300/qt/60/12345_1.jpg`

The same pattern applies to user **avatar** images via `me.avatar`:
```
{cdn_host}/{path}/{name}/re/100x100/qt/60/{name}.jpg
```

---

## 🚫 Anti-Ban & Rate-Limit Strategies

To prevent IP bans or rate limits by the Pepper group firewalls:
1. **User-Agent Rotation:** Randomize browser headers on every session initialization.
2. **Session Persistence:** Retain session cookies (`xsrf_t` and `pepper_session`) across updates rather than re-logging on every call.
3. **Shared Updates (Coordinator):** Fetch all deal types inside a single Home Assistant DataUpdateCoordinator call rather than requesting data individually per entity.
4. **Timeouts:** Restrict all API requests to a `10s` timeout to prevent blocking worker threads in Home Assistant.
5. **Jitter Delay:** Add a random delay (e.g. 1–5 seconds) before each coordinator update cycle to avoid predictable polling fingerprints.
6. **Do NOT use GraphQL introspection:** `__type` queries are immediately blocked (418) — they must never be sent in production code.

---

## 📋 Feature Availability Summary

| Feature | Available | Auth Required | Notes |
| :--- | :---: | :---: | :--- |
| Hot deals (`hottestWidget`) | ✅ | ❌ | Best deals of the day |
| Chronological deals (`threads`) | ✅ | ❌ | Newest deals feed |
| Freebies filter | ✅ | ❌ | `isFreebies: true` in filter |
| Vouchers filter | ✅ | ❌ | `isVoucher: true` in filter |
| Deal: price | ✅ | ❌ | |
| Deal: next best price | ✅ | ❌ | Historical comparison price |
| Deal: temperature | ✅ | ❌ | Heat score |
| Deal: voucher code | ✅ | ❌ | Field: `voucherCode` |
| Deal: type (Deal/Voucher/Freebie) | ✅ | ❌ | Field: `type` |
| Deal: expired status | ✅ | ❌ | Fields: `isExpired`, `expirable` |
| Deal: comment count | ✅ | ❌ | Field: `commentCount` |
| Deal: share count | ✅ | ❌ | Field: `shareCount` |
| Deal: submitter username | ✅ | ❌ | Field: `user.username` |
| Deal: merchant page URL | ✅ | ❌ | Field: `merchant.merchantPageUrl` |
| Deal: featured/picked timestamp | ✅ | ❌ | Field: `pickedAt` |
| User profile | ✅ | ✅ | `me` query |
| User karma | ❌ | — | Removed from API |
| User notifications count | ❌ | — | Removed from API |
| User conversations count | ❌ | — | Removed from API |
| User thread count | ✅ | ✅ | `me.threadCount` |
| User comment count | ✅ | ✅ | `me.commentCount` |
| User avatar | ✅ | ✅ | `me.avatar` |
| User badges | ✅ | ✅ | `me.badges` |
| Keyword/deal search | ✅ | ❌ | HTML scraping (no GraphQL endpoint) |
| GraphQL introspection | ❌ | — | Blocked by WAF (418) |
