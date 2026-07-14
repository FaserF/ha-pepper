# Configuration

This integration is fully configured via the Home Assistant User Interface.

## Setup Steps

1. Navigate to **Settings** > **Devices & Services** in Home Assistant.
2. Click **Add Integration** in the bottom-right corner.
3. Search for **MyDealz** and select it.
4. Set the following options:
   - **Sort Mode**:
     - `hot`: Retrieve deals sorted by votes/temperature.
     - `new`: Retrieve the newest deals.
   - **Scan Interval**: The number of minutes to wait between updates (default: `15` minutes). We recommend keeping it at `15` or above to prevent rate-limiting by MyDealz's Cloudflare WAF.
5. Click **Submit** to finalize the setup.
