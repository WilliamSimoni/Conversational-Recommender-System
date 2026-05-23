import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_categories() -> dict:
    config_path = (
        Path(__file__).resolve().parent.parent.parent / "data" / "categories.json"
    )
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)
