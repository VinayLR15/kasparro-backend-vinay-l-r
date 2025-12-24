import csv
from typing import Iterator, Dict, Any
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

class CSVSource:
    def __init__(self, path: str = None):
        self.path = Path(path) if path else DATA_DIR / "assets.csv"

    def list_assets(self) -> Iterator[Dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                yield {"id": row.get("id") or row.get("external_id") or row.get("symbol"), "symbol": row.get("symbol"), "name": row.get("name"), "raw": row}
