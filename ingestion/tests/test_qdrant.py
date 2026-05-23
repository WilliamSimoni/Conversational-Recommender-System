import uuid
from unittest.mock import MagicMock, patch

from crs_ingestion.models import ProductPayload
from crs_ingestion.qdrant import get_deterministic_uuid, load_to_qdrant


def test_deterministic_uuid():
    uid = get_deterministic_uuid("p_001")
    assert isinstance(uid, str)
    assert uuid.UUID(uid)
    assert get_deterministic_uuid("p_001") == uid


@patch("crs_ingestion.qdrant.QdrantClient")
def test_load_to_qdrant(mock_qdrant_client):
    mock_client = MagicMock()
    mock_qdrant_client.return_value = mock_client

    payloads = [
        ProductPayload(
            product_id="p_1",
            title="Prod 1",
            description_clean="Clean",
            has_in_stock_variant=True,
            available=True,
        )
    ]
    vectors = [[0.1, 0.2]]

    load_to_qdrant(
        payloads=payloads,
        vectors=vectors,
        qdrant_url="http://localhost:6333",
        qdrant_api_key="fake-key",
        collection_name="test-collection",
    )

    mock_qdrant_client.assert_called_once_with(
        url="http://localhost:6333", api_key="fake-key"
    )
    # Check recreate_collection or check if collection exists and creation logic
    mock_client.collection_exists.assert_called_once_with("test-collection")
    mock_client.upsert.assert_called_once()
