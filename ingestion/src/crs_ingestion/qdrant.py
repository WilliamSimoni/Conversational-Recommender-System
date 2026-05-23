import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from crs_ingestion.models import ProductPayload


def get_deterministic_uuid(product_id: str) -> str:
    namespace = uuid.UUID("12345678-1234-5678-1234-567812345678")
    return str(uuid.uuid5(namespace, product_id))


def load_to_qdrant(
    payloads: list[ProductPayload],
    vectors: list[list[float]],
    qdrant_url: str,
    qdrant_api_key: str | None,
    collection_name: str,
    vector_size: int = 1536,
) -> None:
    if not payloads or not vectors:
        return

    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    points = []
    for payload, vector in zip(payloads, vectors):
        point_id = get_deterministic_uuid(payload.product_id)
        points.append(
            PointStruct(id=point_id, vector=vector, payload=payload.model_dump())
        )

    client.upsert(collection_name=collection_name, points=points, wait=True)
