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
    # Added from dev.env
    SANATANA_MCP_API_URL: Optional[str] = None
    LLM_PROVIDER: Optional[str] = None
    # Azure parameters
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = None
    AZURE_REASONING_MODEL: Optional[str] = None
    AZURE_SUMMARIZING_MODEL: Optional[str] = None
    AZURE_PLANNER_MODEL: Optional[str] = None
    AZURE_OPENAI_KEY: Optional[str] = None
    # Open AI parameters 
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_REASONING_MODEL: Optional[str] = None
    OPENAI_SUMMARIZING_MODEL: Optional[str] = None
    OPENAI_PLANNER_MODEL: Optional[str] = None

    model_config = {
        "env_file": os.path.join(os.path.dirname(__file__), "dev.env")
    }

config: AppConfig = AppConfig()
