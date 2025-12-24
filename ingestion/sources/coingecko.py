import requests
from typing import Iterator, Dict, Any

API_BASE = "https://api.coingecko.com/api/v3"

class CoinGeckoSource:
    def __init__(self):
        self.session = requests.Session()

    def list_assets(self) -> Iterator[Dict[str, Any]]:
        url = f"{API_BASE}/coins/list"
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        for item in resp.json():
            yield {"id": item.get("id"), "symbol": item.get("symbol"), "name": item.get("name"), "raw": item}
