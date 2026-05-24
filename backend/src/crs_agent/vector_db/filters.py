from qdrant_client.http import models

from crs_agent.vector_db.models import VectorSearchInput

CATEGORY_MAP: dict[str, list[str]] = {
    "fragranze": ["Perfumes & Colognes", "Aftershave", "Deodorants"],
    "skincare": ["Skin Care", "Bath & Body"],
    "make-up": ["Makeup", "Cosmetic Sets", "Cosmetic Tools", "Nail Care"],
    "capelli": [
        "Shampoo & Conditioner",
        "Hair Treatments",
        "Hair Styling Products",
        "Hair Styling Tools",
        "Beard Combs & Brushes",
    ],
    "altro": ["Mouthwash", "Shaving Soap", "Candles", "Household Cleaning Products"],
}


def build_filter(query: VectorSearchInput) -> models.Filter:
    must = []
    must_not = []

    variant_conditions = []

    if not query.include_oos:
        variant_conditions.append(
            models.FieldCondition(
                key="available",
                match=models.MatchValue(value=True),
            )
        )
    if query.budget_max_eur is not None:
        variant_conditions.append(
            models.FieldCondition(
                key="price_eur",
                range=models.Range(lte=query.budget_max_eur),
            )
        )
    if query.budget_min_eur is not None:
        variant_conditions.append(
            models.FieldCondition(
                key="price_eur",
                range=models.Range(gte=query.budget_min_eur),
            )
        )

    if variant_conditions:
        must.append(
            models.NestedCondition(
                nested=models.Nested(
                    key="variants",
                    filter=models.Filter(must=variant_conditions),
                )
            )
        )

    if query.category is not None:
        must.append(
            models.FieldCondition(
                key="category_l4",
                match=models.MatchAny(any=CATEGORY_MAP[query.category]),
            )
        )

    if query.is_niche is not None:
        must.append(
            models.FieldCondition(
                key="is_niche",
                match=models.MatchValue(value=query.is_niche),
            )
        )

    if query.exclude_product_ids:
        must_not.append(
            models.FieldCondition(
                key="product_id",
                match=models.MatchAny(any=query.exclude_product_ids),
            )
        )

    return models.Filter(
        must=must if must else None,
        must_not=must_not if must_not else None,
    )
