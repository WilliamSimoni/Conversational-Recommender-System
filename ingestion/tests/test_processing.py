from crs_ingestion.processing import build_enriched_text, parse_raw_product


def test_parse_raw_product():
    raw_data = {
        "product_id": "p_001",
        "title": "Lumé, kit solari 2025",
        "description": "<p>Proteggi la tua pelle con il kit solari 2025.</p>",
        "collections": ["prodotti", "profumi-di-nicchia-donna", "all"],
        "min_price_eur": 113.99,
        "max_price_eur": 113.99,
        "available": False,
        "variants": [
            {
                "variant_id": "p_001_v1",
                "title": "Default Title",
                "price_eur": 113.99,
                "available": False,
            }
        ],
        "custom_fields": [
            {"key": "collezione", "value": "gid://shopify/Collection/506804207780"},
            {"key": "tipologia_prodotto", "value": "Eau de Parfum"},
            {"key": "ingredienti", "value": "Alcohol, <b>Aqua</b>"},
        ],
        "productCategory": {
            "l1": "Health & Beauty",
            "l2": "Personal Care",
            "l3": "Cosmetics",
            "l4": "Skin Care",
            "fullPath": "Health & Beauty > Personal Care > Cosmetics > Skin Care",
        },
    }

    payload = parse_raw_product(raw_data)

    assert payload.product_id == "p_001"
    assert payload.title == "Lumé, kit solari 2025"
    assert payload.category_l4 == "Skin Care"
    assert (
        payload.category_path
        == "Health & Beauty > Personal Care > Cosmetics > Skin Care"
    )
    assert payload.product_type == "Eau de Parfum"
    assert payload.description_clean == "Proteggi la tua pelle con il kit solari 2025."
    assert payload.ingredients_clean == "Alcohol, Aqua"
    assert payload.collection_id == "gid://shopify/Collection/506804207780"
    assert payload.is_niche is True
    assert payload.available is False
    assert payload.has_in_stock_variant is False
    assert len(payload.variants) == 1
    assert payload.variants[0].title is None


def test_build_enriched_text():
    raw_data = {
        "product_id": "p_001",
        "title": "Lumé, kit solari 2025",
        "description": "<p>Proteggi la tua pelle con il kit solari 2025.</p>",
        "collections": ["prodotti", "fragranze-di-nicchia", "all"],
        "min_price_eur": 113.99,
        "max_price_eur": 113.99,
        "available": False,
        "variants": [
            {
                "variant_id": "p_001_v1",
                "title": "20ml",
                "price_eur": 113.99,
                "available": False,
            }
        ],
        "custom_fields": [
            {"key": "tipologia_prodotto", "value": "Eau de Parfum"},
            {"key": "ingredienti", "value": "Alcohol, Aqua"},
        ],
        "productCategory": {
            "l4": "Skin Care",
            "fullPath": "Health & Beauty > Personal Care > Cosmetics > Skin Care",
        },
    }
    payload = parse_raw_product(raw_data)
    enriched = build_enriched_text(payload)

    assert "Title: Lumé, kit solari 2025" in enriched
    assert "Category: Skin Care" in enriched
    assert "Type: Eau de Parfum" in enriched
    assert "Description: Proteggi la tua pelle con il kit solari 2025." in enriched
    assert "Ingredients: Alcohol, Aqua" in enriched
    assert "Collections: prodotti, fragranze-di-nicchia, all" in enriched
    assert "Available Options: 20ml" in enriched
