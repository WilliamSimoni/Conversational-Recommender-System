import json
import logging
import os
from datetime import datetime
from pathlib import Path

from crs_ingestion.processing import build_enriched_text, parse_raw_product
from crs_ingestion.settings import Settings, settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_pipeline(cfg: Settings = settings) -> None:
    catalog_path = cfg.catalog_path
    if not os.path.isabs(catalog_path):
        catalog_path = os.path.abspath(catalog_path)

    logger.info(f"Reading catalog from {catalog_path}")
    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"Catalog file not found at {catalog_path}")

    with open(catalog_path, "r", encoding="utf-8") as f:
        raw_catalog = json.load(f)

    logger.info(f"Loaded {len(raw_catalog)} raw products. Processing payloads...")

    payloads = []
    enriched_texts = []

    for raw_prod in raw_catalog:
        if not isinstance(raw_prod, dict):
            continue
        try:
            payload = parse_raw_product(raw_prod)
            enriched = build_enriched_text(payload)
            payloads.append(payload)
            enriched_texts.append(enriched)
        except Exception as e:
            logger.error(f"Error parsing product {raw_prod.get('product_id')}: {e}")

    logger.info(
        f"Successfully processed {len(payloads)} products. Writing staging file..."
    )

    staging_dir = Path(cfg.staging_folder)
    staging_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    staging_file = staging_dir / f"staging_{timestamp}.jsonl"
    with open(staging_file, "w", encoding="utf-8") as f:
        for payload, enriched in zip(payloads, enriched_texts):
            line = json.dumps(
                {"payload": payload.model_dump(), "enriched_text": enriched},
                ensure_ascii=False,
            )
            f.write(line + "\n")

    logger.info(
        f"Staging written to {staging_file} ({len(payloads)} records). ETL extract+transform completed."
    )


if __name__ == "__main__":
    run_pipeline()
