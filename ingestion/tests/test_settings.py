from crs_ingestion.settings import Settings


def test_settings_loading(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "QDRANT__URL=http://test:6333\n" "QDRANT__API_KEY=test-qdrant-key\n"
    )

    settings = Settings(_env_file=str(env_file))

    assert settings.qdrant.url == "http://test:6333"
    assert settings.qdrant.api_key == "test-qdrant-key"
