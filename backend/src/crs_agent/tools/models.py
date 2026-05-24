from typing import Literal

from pydantic import BaseModel, Field


class SearchCatalogInput(BaseModel):
    query_text: str = Field(
        description=(
            "Rich Italian search string capturing the customer's actual need: scent profile, "
            "occasion, recipient, mood. Expand implicit signals into explicit descriptors. "
            "Exclude price and availability — those go in the filter fields."
        )
    )

    category: Literal["fragranze", "skincare", "make-up", "capelli", "altro"] | None = (
        Field(
            default=None,
            description="Set only when the customer explicitly names a category. Leave None if ambiguous.",
        )
    )

    budget_max_eur: float | None = Field(
        default=None,
        description="Hard price ceiling in EUR. Extract from explicit statements only ('meno di 50€', 'budget 60 euro'). Do not infer from vague terms like 'economico'.",
    )

    budget_min_eur: float | None = Field(
        default=None,
        description="Hard price floor in EUR. Use for 'qualcosa di più luxury' follow-ups or explicit minimums. Rarely needed.",
    )

    is_niche: bool | None = Field(
        default=None,
        description="True for niche/artisanal ('niche', 'esclusivo', 'ricercato'); False for mainstream ('marca famosa'). Leave None if unclear.",
    )

    include_oos: bool = Field(
        default=False,
        description="Include out-of-stock products. True only when customer asks about a specific named product. Always False for open discovery queries.",
    )

    exclude_product_ids: list[str] = Field(
        default=[],
        description="IDs of products already shown this turn. Populate when customer asks for alternatives ('mostrami qualcos'altro').",
    )


class ProductCard(BaseModel):
    """Compact card returned to the agent — keep this tight; it goes back into context."""

    product_id: str
    title: str
    category_l4: str | None
    product_type: str | None
    price_range_eur: str  # "€28.95–€58.52" or "€40.04"
    available: bool  # at least one matching variant in stock
    is_tester: bool
    is_niche: bool
    snippet: str  # first ~200 chars of description_clean
    ingredients_excerpt: str | None = (
        None  # first ~200 chars of ingredients; None when missing
    )
    score: float  # normalized cosine, 0..1


class SearchCatalogOutput(BaseModel):
    results: list[ProductCard]
    total_matched: int  # hits before top_k slicing
    used_filters: dict  # echoed back for debugging in traces
    low_confidence: bool = False  # true when results[0].score < MIN_SCORE_THRESHOLD
