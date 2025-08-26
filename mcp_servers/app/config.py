from typing import Optional
from pydantic_settings import BaseSettings
import os


class AppConfig(BaseSettings):
    PODADMIN_EMAIL: str
    PODADMIN_PASSWORD: str
    LOGFIRE_TOKEN: Optional[str] = None
    LOGFIRE_HOST: Optional[str] = None
    LOGFIRE_CONSOLE_MIN_LOG_LEVEL: Optional[str] = None
    POSTHOG_HOST: Optional[str] = None
    POSTHOG_APIKEY: Optional[str] = None
    BYPASS_TOKEN: str
    # LLM Provider Configuration
    LLM_PROVIDER: Optional[str] = "openai"  # "openai" or "azure"
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_KEY: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = None
    AZURE_MODEL_DEPLOYMENT_NAME: Optional[str] = None
    AZURE_REASONING_MODEL: Optional[str] = None
    AZURE_SUMMARIZING_MODEL: Optional[str] = None
    AZURE_PLANNER_MODEL: Optional[str] = None
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_REASONING_MODEL: Optional[str] = None
    OPENAI_SUMMARIZING_MODEL: Optional[str] = None
    OPENAI_PLANNER_MODEL: Optional[str] = None
    # Embedding Model
    EMBEDDING_MODEL_NAME: Optional[str] = "text-embedding-3-large"
    # Database Configuration
    DB_HOST: Optional[str] = "localhost"
    DB_PORT: Optional[int] = 5432
    DB_NAME: Optional[str] = "sanatana"
    DB_USER: Optional[str] = "postgres"
    DB_PASSWORD: Optional[str] = "postgres995"
    DB_SCHEMA: Optional[str] = "dharma_graph"
    DB_MIN_CONNECTIONS: Optional[int] = 1
    DB_MAX_CONNECTIONS: Optional[int] = 10
    DB_CONNECT_TIMEOUT: Optional[int] = 30
    model_config = {
        "env_file": os.path.join(os.path.dirname(__file__), "dev.env")
    }

config: AppConfig = AppConfig()
