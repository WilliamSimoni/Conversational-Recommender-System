from crs_ingestion.settings import Settings


def test_settings_loading(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=test-openai-key\n"
        "QDRANT_URL=http://localhost:6333\n"
        "QDRANT_API_KEY=test-qdrant-key\n"
        "EMBEDDING_MODEL=test-model\n"
    )

    # Temporarily set the env file path
    settings = Settings(_env_file=str(env_file))

    assert settings.OPENAI_API_KEY == "test-openai-key"
    assert settings.QDRANT_URL == "http://localhost:6333"
    assert settings.QDRANT_API_KEY == "test-qdrant-key"
    assert settings.EMBEDDING_MODEL == "test-model"
