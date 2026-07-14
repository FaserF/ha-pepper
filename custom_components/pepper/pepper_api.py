"""API Client for Pepper undocumented GraphQL API."""

import http.cookiejar
import json
import logging
import random
import urllib.error
import urllib.request
from typing import Any

_LOGGER = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def get_random_headers() -> dict[str, str]:
    """Generate random browser-like headers to mimic a real user session."""
    ua = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    if "Chrome" in ua:
        headers["Sec-CH-UA"] = (
            '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        )
        headers["Sec-CH-UA-Mobile"] = "?0"
        headers["Sec-CH-UA-Platform"] = '"Windows"' if "Windows" in ua else '"macOS"'

    return headers


class PepperAPI:
    """Client for Pepper GraphQL API."""

    def __init__(self, platform: str = "mydealz.de") -> None:
        """Initialize the client."""
        self.platform = platform
        self.base_url = f"https://www.{platform}"
        self.graphql_url = f"{self.base_url}/graphql"
        self.image_host = f"https://static.{platform}"

        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )
        self.xsrf_token: str | None = None
        self._headers = get_random_headers()

    def fetch_session(self) -> None:
        """Fetch the home page to get session cookies and XSRF token."""
        _LOGGER.debug(
            "Fetching Pepper home page to establish session: %s", self.base_url
        )
        # Rotate headers
        self._headers = get_random_headers()
        req = urllib.request.Request(self.base_url, headers=self._headers)
        try:
            with self._opener.open(req, timeout=10) as response:
                response.read()
        except Exception as err:
            _LOGGER.error(
                "Failed to connect to Pepper platform %s: %s", self.platform, err
            )
            raise ConnectionError(
                f"Could not connect to Pepper platform: {err}"
            ) from err

        # Extract xsrf_t cookie
        for cookie in self._cookie_jar:
            if cookie.name == "xsrf_t":
                self.xsrf_token = cookie.value.replace('"', "")
                break

        if not self.xsrf_token:
            raise ValueError("XSRF token (xsrf_t) not found in cookies")

    def _query(self, query_str: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Perform a GraphQL query."""
        if not self.xsrf_token:
            self.fetch_session()

        payload = {"query": query_str, "variables": variables}

        # Adapt browser headers for CORS GraphQL POST request
        headers = self._headers.copy()
        headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Xsrf-Token": self.xsrf_token or "",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
        )
        # Remove navigation headers
        headers.pop("Upgrade-Insecure-Requests", None)
        headers.pop("Sec-Fetch-User", None)

        req = urllib.request.Request(
            self.graphql_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with self._opener.open(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            # Handle Teapot or expired session
            if err.code == 418:
                _LOGGER.info(
                    "Session expired or teapot block (418), re-fetching session"
                )
                self.fetch_session()
                # Retry once
                return self._query(query_str, variables)
            raise ConnectionError(f"HTTP Error {err.code}: {err.reason}") from err
        except Exception as err:
            _LOGGER.error("Query failed: %s", err)
            raise ConnectionError(f"Failed to execute query: {err}") from err

        if "errors" in res_data and res_data["errors"]:
            err_msg = res_data["errors"][0].get("message", "Unknown GraphQL error")
            _LOGGER.error("GraphQL errors: %s", res_data["errors"])
            raise ValueError(f"GraphQL Query Error: {err_msg}")

        return res_data.get("data", {})

    def get_deals(self, sort_mode: str = "hot") -> list[dict[str, Any]]:
        """Fetch deals with sorting mode 'hot' or 'new'."""
        query = """
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
        """

        variables = {"filter": {"sort": {"eq": sort_mode}}}

        data = self._query(query, variables)
        threads = data.get("threads", [])

        deals = []
        for t in threads:
            # Build clean image URL
            image_url = None
            main_img = t.get("mainImage")
            if main_img and main_img.get("path") and main_img.get("name"):
                path = main_img["path"]
                name = main_img["name"]
                image_url = (
                    f"{self.image_host}/{path}/{name}/re/300x300/qt/60/{name}.jpg"
                )

            merchant_name = None
            merchant = t.get("merchant")
            if merchant:
                merchant_name = merchant.get("merchantName")

            deal = {
                "id": t.get("threadId"),
                "title": t.get("title"),
                "url": t.get("url"),
                "price": t.get("price"),
                "temperature": t.get("temperature"),
                "published_at": t.get("publishedAt"),
                "created_at": t.get("createdAt"),
                "description": t.get("description"),
                "merchant": merchant_name,
                "image_url": image_url,
            }
            deals.append(deal)

        return deals
