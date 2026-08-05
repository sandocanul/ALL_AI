from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Baza de date
    database_url: str = "sqlite:///./app.db"

    # Auth
    secret_key: str = "schimba-acest-secret-in-productie"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 zile

    # Chei API modele AI
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Costuri credite per model
    groq_credit_cost: float = 1
    gemini_credit_cost: float = 5
    openai_credit_cost: float = 10
    anthropic_credit_cost: float = 8

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_credits: str = ""
    frontend_url: str = "http://localhost:5500"

    # Vector DB (memorie comuna / RAG)
    vector_db_type: str = "chroma"
    chroma_persist_dir: str = "./chroma_data"

    # Configurarea pentru Pydantic v2
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()