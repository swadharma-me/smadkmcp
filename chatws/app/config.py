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
    FIREBASE_SERVICE_CREDENTIALS:str
    FIREBASE_API_KEY: str
    FIREBASE_AUTH_DOMAIN: str
    FIREBASE_AUTH_URL: str
    # Open AI
    GOOGLE_ADK_API_URL:str

    model_config = {
        "env_file": os.path.join(os.path.dirname(__file__), "dev.env")
    }

config: AppConfig = AppConfig()
