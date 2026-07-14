# MyDealz Undocumented GraphQL API Documentation

This document describes the findings and implementation details of the private, undocumented GraphQL API of **MyDealz.de**.

## Authentication & CSRF Bypass (Anti-Teapot Flow)

Direct POST requests to `https://www.mydealz.de/graphql` are protected by a Cloudflare WAF/security layer and return `HTTP 418 I'm a teapot` with error message `{"message":"Whiiiiiiieeee","data":[]}` if the request lacks a valid session and CSRF token.

To bypass this check:
1. **Initialize Session:** Perform a GET request to the homepage `https://www.mydealz.de/`.
2. **Extract Cookies:** Save the cookies returned in the response, notably `pepper_session` and `xsrf_t`.
3. **Add Headers:** For all subsequent POST requests to `/graphql`:
   - Send the extracted cookies in the `Cookie` header.
   - Send the extracted `xsrf_t` token in the `X-Xsrf-Token` header.
   - Send `X-Requested-With: XMLHttpRequest` header.

---

## GraphQL Schema & Queries

### 1. Fetching Deal Listings (`threads`)

The listing of deals is retrieved using the `threads` query. It takes a required `filter` of type `ThreadFilter!`.

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
      merchantId
      merchantName
    }
    mainImage {
      uid
      path
      name
      ext
    }
  }
}
```

#### Variables
Passing an empty filter returns the default list of newest deals:
```json
{
  "filter": {}
}
```

To fetch deals sorted by hotness, use the `sort` field:
```json
{
  "filter": {
    "sort": { "eq": "hot" }
  }
}
```

---

## Data Structure Reference

### Type `Thread`
- `threadId` (String): Unique ID of the deal thread.
- `title` (String): Deal title.
- `url` (String): Canonical URL to the deal.
- `price` (Float): Price of the product (can be `null` for freebies/contracts).
- `temperature` (Float): Deal heat/votes in degrees (e.g. `120.5`).
- `publishedAt` (Int): Timestamp (UNIX) of publishing.
- `createdAt` (Int): Timestamp (UNIX) of thread creation.
- `description` (String): Full deal description formatted as HTML.
- `merchant` (`Merchant`): Product vendor.
- `mainImage` (`PicsyImage`): Featured deal image.

### Type `Merchant`
- `merchantId` (String): Unique ID of the merchant.
- `merchantName` (String): Name of the merchant (e.g., "Amazon", "Fritz Berger").

### Type `PicsyImage`
- `uid` (String): Image unique identifier.
- `path` (String): Subpath on the static CDN.
- `name` (String): Base name of the image.
- `ext` (String): Image file extension.

### Static Image CDN URLs
Images are hosted on `https://static.mydealz.de`. Using the `PicsyImage` subfields, the URL of the image can be dynamically constructed as:
```
https://static.mydealz.de/{path}/{name}/re/300x300/qt/60/{name}.jpg
```
Where `re/300x300/qt/60` is the thumbnail resizing and quality profile used by the frontend.
