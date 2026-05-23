from typing import Any

from crs_ingestion.categories import load_categories
from crs_ingestion.cleaning import clean_text, strip_html
from crs_ingestion.models import ProductPayload, Variant


def parse_raw_product(raw: dict[str, Any]) -> ProductPayload:
    # 1. extract product title
    product_id = raw.get("product_id", "")
    title = clean_text(raw.get("title", ""))

    # 2. Extract description and clean/strip HTML
    description_raw = raw.get("description")
    description_clean = strip_html(description_raw)

    # 3. Extract category l4 & path
    category_l4 = None
    category_path = None
    category_raw = raw.get("productCategory")
    if isinstance(category_raw, dict):
        category_l4 = clean_text(category_raw.get("l4"))
        category_path = clean_text(category_raw.get("fullPath"))
        if not category_l4:
            category_l4 = None
        if not category_path:
            category_path = None

    # 4. Extract custom fields
    product_type = None
    ingredients_clean = None
    collection_id = None

    custom_fields = raw.get("custom_fields") or []

    for field in custom_fields:
        if not isinstance(field, dict):
            continue
        key = field.get("key")
        val = field.get("value")
        if not val:
            continue

        if key == "tipologia_prodotto":
            product_type = clean_text(str(val))
        elif key == "ingredienti":
            ingredients_clean = strip_html(str(val))
        elif key == "collezione":
            collection_id = clean_text(str(val))

    # 5. Extract raw collections
    raw_collections_raw = raw.get("collections") or []
    raw_collections = [clean_text(c) for c in raw_collections_raw if c]

    # 6. Detect tester: title starts with "T."
    is_tester = bool(title and title.strip().startswith("T."))

    # 7. Detect is_niche: exact match against whitelist in config
    config = load_categories()
    niche_collections = set(config.get("niche", {}).get("positive_collections", []))
    is_niche = any(c in niche_collections for c in raw_collections)

    # 8. Map variants
    variants_list = []
    raw_variants = raw.get("variants") or []
    for var in raw_variants:
        if not isinstance(var, dict):
            continue
        var_id = var.get("variant_id", "")
        v_title_raw = var.get("title", "")
        v_title = clean_text(v_title_raw) if v_title_raw else None

        if v_title == "Default Title":
            v_title = None

        price_eur = float(var.get("price_eur") or 0.0)
        available_status = bool(var.get("available", False))

        variants_list.append(
            Variant(
                variant_id=var_id,
                title=v_title,
                price_eur=price_eur,
                available=available_status,
            )
        )

    # 9. Available states & prices
    available = bool(raw.get("available", False))
    has_in_stock_variant = any(v.available for v in variants_list)

    min_price_eur = raw.get("min_price_eur")
    if min_price_eur is not None:
        min_price_eur = float(min_price_eur)
    max_price_eur = raw.get("max_price_eur")
    if max_price_eur is not None:
        max_price_eur = float(max_price_eur)

    return ProductPayload(
        product_id=product_id,
        title=title,
        category_l4=category_l4,
        category_path=category_path,
        product_type=product_type,
        description_clean=description_clean,
        ingredients=ingredients_clean,
        collection_id=collection_id,
        raw_collections=raw_collections,
        is_niche=is_niche,
        is_tester=is_tester,
        has_in_stock_variant=has_in_stock_variant,
        available=available,
        min_price_eur=min_price_eur,
        max_price_eur=max_price_eur,
        variants=variants_list,
    )


def build_enriched_text(payload: ProductPayload) -> str:
    parts = []
    if payload.title:
        parts.append(f"Title: {payload.title}")
    if payload.category_l4:
        parts.append(f"Category: {payload.category_l4}")
    if payload.product_type:
        parts.append(f"Type: {payload.product_type}")
    if payload.description_clean:
        parts.append(f"Description: {payload.description_clean}")
    if payload.is_tester:
        parts.append(
            "Note: This is a tester unit — not in original packaging, usually cheaper."
        )
    if payload.ingredients:
        parts.append(f"Ingredients: {payload.ingredients}")
    if payload.raw_collections:
        parts.append(f"Collections: {', '.join(payload.raw_collections)}")
    if payload.variants:
        variant_titles = [v.title for v in payload.variants if v.title]
        if variant_titles:
            unique_variants = list(dict.fromkeys(variant_titles))
            parts.append(f"Available Options: {', '.join(unique_variants)}")
    return "\n".join(parts)
