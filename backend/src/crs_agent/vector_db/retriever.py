import logging

from qdrant_client import AsyncQdrantClient
from tenacity import retry, stop_after_attempt, wait_exponential

from crs_agent.settings import settings
from crs_agent.vector_db.embeddings import embeddings_model
from crs_agent.vector_db.filters import build_filter
from crs_agent.vector_db.models import ScoredProductPayload, VectorSearchInput

logger = logging.getLogger(__name__)

qdrant = AsyncQdrantClient(
    url=settings.qdrant.url,
    api_key=settings.qdrant.api_key,
)

COLLECTION_NAME = settings.qdrant.collection_name


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _execute_qdrant_query(query: VectorSearchInput) -> list[ScoredProductPayload]:
    query_vector = await embeddings_model.aembed_query(query.query_text)

    search_response = await qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=build_filter(query),
        limit=query.top_k,
        with_payload=True,
    )

    return [
        ScoredProductPayload(**hit.payload, score=hit.score)
        for hit in search_response.points
    ]


async def retrieve_by_product_ids(product_ids: list[str]) -> list[ScoredProductPayload]:
    """Retrieve products by their product_ids from Qdrant."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    if not product_ids:
        return []

    try:
        search_response = await qdrant.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                should=[
                    FieldCondition(
                        key="product_id",
                        match=MatchValue(value=pid),
                    )
                    for pid in product_ids
                ]
            ),
            limit=len(product_ids),
            with_payload=True,
        )
        points = search_response[0]
        return [ScoredProductPayload(**hit.payload, score=1.0) for hit in points]
    except Exception as e:
        logger.error(f"Qdrant retrieve failed for product_ids '{product_ids}': {e}")
        raise


async def execute_qdrant_query(query: VectorSearchInput) -> list[ScoredProductPayload]:
    """Public entry point. Wraps the retried inner call."""
    try:
        return await _execute_qdrant_query(query)
    except Exception as e:
        logger.error(
            f"Qdrant query failed after retries for query '{query.query_text}': {e}"
        )
        raise
