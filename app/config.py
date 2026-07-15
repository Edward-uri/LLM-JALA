import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.path.join(RAIZ_PROYECTO, ".env"))

    ollama_url: str
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout_s: float = 30.0
    llm_jala_api_key: Optional[str] = None  # si se define, /clasificar exige X-API-Key

settings = Settings()
