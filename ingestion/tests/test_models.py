from crs_ingestion.models import ProductPayload, Variant


def test_variant_model():
    v = Variant(variant_id="v1", title="Default Title", price_eur=12.50, available=True)
    assert v.variant_id == "v1"
    assert v.title == "Default Title"


def test_product_payload():
    p = ProductPayload(
        product_id="p1",
        title="Test Product",
        category_l4="Skin Care",
        category_path="Health > Skin Care",
        product_type="Cream",
        description_clean="Clean description.",
        ingredients_clean="Water, Glycerin",
        collection_id="col1",
        raw_collections=["c1", "c2"],
        is_niche=True,
        has_in_stock_variant=True,
        available=True,
        min_price_eur=10.0,
        max_price_eur=15.0,
        variants=[],
    )
    assert p.product_id == "p1"
    assert p.schema_version == "v1"
