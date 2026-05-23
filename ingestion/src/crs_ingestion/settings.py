import os
from pathlib import Path
from typing import Tuple, Type

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

BACKEND_ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = os.getenv("CONFIG_PATH", BACKEND_ROOT_DIR / "config.yaml")
ENV_PATH = os.getenv("ENV_PATH", BACKEND_ROOT_DIR / ".env")


class EmbeddingModelConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str | None = None
    model_name: str = "text-embedding-3-small"


class QdrantConfig(BaseModel):
    url: str = "http://localhost:6333"
    api_key: str | None = None
    collection_name: str = "chatwilly_brain"
    vector_size: int = 1536


class Settings(BaseSettings):
    catalog_path: str = "data/catalog.json"
    staging_folder: str = "./staging"
    debug: bool = False
    embedding_model: EmbeddingModelConfig = EmbeddingModelConfig()
    qdrant: QdrantConfig = QdrantConfig()

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        yaml_file=CONFIG_PATH,
        yaml_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """
        Define the sources and their precedence.
        The first item in the tuple has the highest precedence.
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
        )


settings = Settings()
