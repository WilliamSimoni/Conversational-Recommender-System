from typing import Literal

from pydantic import BaseModel, Field


class VectorSearchInput(BaseModel):
    query_text: str
    category: Literal["fragranze", "skincare", "make-up", "capelli", "altro"] | None = (
        None
    )
    budget_max_eur: float | None = None
    budget_min_eur: float | None = None
    is_niche: bool | None = None
    include_oos: bool = False
    top_k: int = 10
    exclude_product_ids: list[str] = Field(default_factory=list)


class Variant(BaseModel):
    variant_id: str
    title: str | None
    price_eur: float
    available: bool


class ProductPayload(BaseModel):
    schema_version: Literal["v1"] = "v1"
    product_id: str
    title: str
    category_l4: str | None = None
    category_path: str | None = None
    product_type: str | None = None
    description_clean: str
    ingredients: str | None = None
    collection_id: str | None = None
    raw_collections: list[str] = Field(default_factory=list)
    is_niche: bool = False
    is_tester: bool = False
    has_in_stock_variant: bool
    available: bool
    min_price_eur: float | None = None
    max_price_eur: float | None = None
    variants: list[Variant] = Field(default_factory=list)


class ScoredProductPayload(ProductPayload):
    score: float
