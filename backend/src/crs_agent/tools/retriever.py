import logging

from crs_agent.settings import settings
from crs_agent.tools.models import ProductCard, SearchCatalogInput, SearchCatalogOutput
from crs_agent.vector_db.models import ScoredProductPayload, VectorSearchInput
from crs_agent.vector_db.retriever import execute_qdrant_query
from langchain.tools import tool

logger = logging.getLogger(__name__)

MIN_SCORE_THRESHOLD = settings.search_min_score_threshold


def _to_vector_search_input(query: SearchCatalogInput) -> VectorSearchInput:
    return VectorSearchInput(
        query_text=query.query_text,
        category=query.category,
        budget_max_eur=query.budget_max_eur,
        budget_min_eur=query.budget_min_eur,
        is_niche=query.is_niche,
        include_oos=query.include_oos,
        top_k=10,
        exclude_product_ids=query.exclude_product_ids,
    )


def _assemble_product_card(
    payload: ScoredProductPayload, query: SearchCatalogInput
) -> ProductCard:
    matching_variants = [
        v
        for v in payload.variants
        if v.available
        and (query.budget_max_eur is None or v.price_eur <= query.budget_max_eur)
        and (query.budget_min_eur is None or v.price_eur >= query.budget_min_eur)
    ]

    prices = [v.price_eur for v in matching_variants]
    if prices:
        price_range = (
            f"€{min(prices):.2f}"
            if min(prices) == max(prices)
            else f"€{min(prices):.2f}–€{max(prices):.2f}"
        )
    else:
        price_range = "N/A"

    return ProductCard(
        product_id=payload.product_id,
        title=payload.title,
        category_l4=payload.category_l4,
        product_type=payload.product_type,
        price_range_eur=price_range,
        available=bool(matching_variants),
        is_tester=payload.is_tester,
        is_niche=payload.is_niche,
        snippet=payload.description_clean[:200],
        ingredients_excerpt=payload.ingredients[:200] if payload.ingredients else None,
        score=round(payload.score, 4),
    )


@tool
async def retrieve_products(query: SearchCatalogInput) -> SearchCatalogOutput | str:
    """
    Search the product catalog and return matching ProductCards.

    You can use this tool to explore the catalog or find specific items.
    However, if the user's initial request is very broad (e.g., "I need a gift" or "I want a perfume")
    and returns too many generic results, DO NOT recommend them immediately.
    Instead, use the AskClarification action to narrow down their preferences (budget, notes, occasion).

    Re-call with refined filters when:
    - no results match the budget (relax or surface alternatives)
    - customer wanted niche but results were mass-market (set is_niche=True)
    - customer asks for alternatives (populate exclude_product_ids from last_recommendations in CONTEXT)
    - customer refines with 'più luxury' / 'più economico' (adjust budget_min/max based on CONTEXT prices)

    Do NOT call for purely informational questions (brand history, ingredients,
    store policies, order status) — those go to Escalate.
    """
    try:
        hits = await execute_qdrant_query(_to_vector_search_input(query))
        cards = [_assemble_product_card(hit, query) for hit in hits]
        top_score = cards[0].score if cards else 0.0

        return SearchCatalogOutput(
            results=cards,
            total_matched=len(cards),
            used_filters=query.model_dump(
                include={
                    "category",
                    "budget_max_eur",
                    "budget_min_eur",
                    "is_niche",
                    "include_oos",
                    "exclude_product_ids",
                }
            ),
            low_confidence=top_score < MIN_SCORE_THRESHOLD,
        )
    except Exception as e:
        logger.error(
            f"Catalog search failed after retries for query '{query.query_text}': {e}"
        )
        return (
            "SYSTEM WARNING: The product catalog is currently unavailable. "
            "Do not attempt further searches. "
            "Apologize to the customer in brand voice and offer to escalate to a human agent."
        )
