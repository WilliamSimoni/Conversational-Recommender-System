import functools
from pathlib import Path


@functools.lru_cache(maxsize=1)
def get_brand_guidelines() -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "brand.md"
    return path.read_text(encoding="utf-8")
