import argparse
import json
import logging
from pathlib import Path

from crs_ingestion.embeddings import embeddings_model
from crs_ingestion.models import ProductPayload
from crs_ingestion.qdrant import load_to_qdrant
from crs_ingestion.settings import Settings, settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_load(staging_name: str | None = None, cfg: Settings = settings) -> None:
    staging_dir = Path(cfg.staging_folder)
    if staging_name:
        staging_file = staging_dir / staging_name
        if not staging_file.exists():
            raise FileNotFoundError(f"Staging file not found at {staging_file}")
    else:
        staging_files = sorted(staging_dir.glob("staging_*.jsonl"), reverse=True)
        if not staging_files:
            raise FileNotFoundError(f"No staging files found in {staging_dir}")
        staging_file = staging_files[0]

    logger.info(f"Reading staging file from {staging_file}")

    payloads: list[ProductPayload] = []
    enriched_texts: list[str] = []

    with open(staging_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            payload = ProductPayload.model_validate(record["payload"])
            payloads.append(payload)
            enriched_texts.append(record["enriched_text"])

    logger.info(
        f"Loaded {len(payloads)} records from staging. Generating embeddings..."
    )

    batch_size = cfg.embedding_model.embedding_batch_size
    vectors: list[list[float]] = []
    for i in range(0, len(enriched_texts), batch_size):
        batch = enriched_texts[i : i + batch_size]
        vectors.extend(embeddings_model.embed_documents(batch))
        logger.info(
            f"  Embedded batch {i // batch_size + 1}/{(len(enriched_texts) + batch_size - 1) // batch_size}"
        )

    vector_size = len(vectors[0]) if vectors else cfg.qdrant.vector_size
    logger.info(
        f"Generated {len(vectors)} vectors of dimension {vector_size}. Loading to Qdrant..."
    )

    load_to_qdrant(
        payloads=payloads,
        vectors=vectors,
        qdrant_url=cfg.qdrant.url,
        qdrant_api_key=cfg.qdrant.api_key,
        collection_name=cfg.qdrant.collection_name,
        vector_size=vector_size,
    )

    logger.info("Load phase completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load staged data to Qdrant")
    parser.add_argument(
        "staging_name",
        nargs="?",
        default=None,
        help="Specific staging filename (e.g. staging_2026-05-23T14-30-00.jsonl)",
    )
    args = parser.parse_args()
    run_load(staging_name=args.staging_name)
