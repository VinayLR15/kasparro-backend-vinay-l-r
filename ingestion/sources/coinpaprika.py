import requests
from typing import Iterator, Dict, Any, Optional
from core.config import settings

API_BASE = "https://api.coinpaprika.com/v1"

class CoinPaprikaSource:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.COINPAPRIKA_API_KEY
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"x-api-key": self.api_key})

    def list_assets(self) -> Iterator[Dict[str, Any]]:
        url = f"{API_BASE}/coins"
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        for item in resp.json():
            yield {"id": item.get("id"), "symbol": item.get("symbol"), "name": item.get("name"), "raw": item}
