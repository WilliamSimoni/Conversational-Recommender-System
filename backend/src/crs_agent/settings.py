import os
from pathlib import Path
from typing import Tuple, Type

from pydantic import BaseModel, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

BACKEND_ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = os.getenv("CONFIG_PATH", BACKEND_ROOT_DIR / "config.yaml")
ENV_PATH = os.getenv("ENV_PATH", BACKEND_ROOT_DIR / ".env")


class RedisConfig(BaseModel):
    enabled: bool = False
    url: str = "redis://localhost:6379"


class AIModelConfig(BaseModel):
    """Connection details only — what to connect to."""

    base_url: str = None
    api_key: str | None = None
    model_name: str = "unknown"
    reasoning_model: bool = False


class ModelRoleConfig(BaseModel):
    """Role assignment + generation behavior"""

    model: str
    fallback: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    reasoning_effort: str | None = None


class EmbeddingModelConfig(BaseModel):
    base_url: str = None
    api_key: str | None = None
    model_name: str = "text-embedding-3-small"


class QdrantConfig(BaseModel):
    url: str = "http://localhost:6333"
    api_key: str | None = None
    collection_name: str = "crs_data"
    vector_size: int = 1536


class PostgresConfig(BaseModel):
    enabled: bool = False
    url: str = "postgresql://user:password@localhost:5432/crs"


class Settings(BaseSettings):
    """
    Loads configuration from config.yaml and allows override via environment variables.
    Precedence (highest to lowest):
      1. Environment variables (e.g. DATABASE__REDIS_URL)
      2. Values in config.yaml
      3. Hardcoded default values
    """

    app_name: str = "Cierge"
    app_version: str = "1.0.0"
    app_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    # Map the nested configuration
    qdrant: QdrantConfig = QdrantConfig()
    postgres: PostgresConfig = PostgresConfig()

    # Root level configurations
    debug: bool = False

    graph_max_input_characters_per_message: int = 16000

    models: dict[str, AIModelConfig] = {}

    orchestrator_model: ModelRoleConfig
    ask_model: ModelRoleConfig
    recommend_model: ModelRoleConfig

    orchestrator_agent_max_iterations: int = 5
    main_loop_max_iterations: int = 5

    embedding_model: EmbeddingModelConfig = EmbeddingModelConfig()

    search_min_score_threshold: float = 0.4

    # Configure Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        yaml_file=CONFIG_PATH,
        yaml_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_model_references(self) -> "Settings":
        roles = [self.orchestrator_model, self.ask_model, self.recommend_model]
        for role in roles:
            for ref in (role.model, role.fallback):
                if ref is not None and ref not in self.models:
                    raise ValueError(
                        f"Model '{ref}' is referenced but not defined in settings.models"
                    )
        return self

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
