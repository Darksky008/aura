"""Central, environment-driven configuration. Nothing here is ever sent to the browser."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"  # development | production
    log_level: str = "INFO"

    # --- Database -------------------------------------------------------------
    database_url: str = "postgresql+psycopg://aura:aura@localhost:5432/aura"
    restaurant_database_path: str = "database/aura_restaurant.db"
    auto_create_tables: bool = True  # create tables on boot (swap for Alembic later)
    auto_seed: bool = False  # seed demo hotel on boot when the DB is empty

    # --- Groq (LLM + speech-to-text) -------------------------------------------
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_reasoning_effort: str = "low"  # only sent to openai/gpt-oss* models
    groq_stt_model: str = "whisper-large-v3"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    llm_timeout_seconds: float = 40.0
    stt_min_confidence: float = 0.22  # exp(avg_logprob) below this => "please repeat"

    # --- Voice output ---------------------------------------------------------
    tts_provider: str = "auto"  # auto | azure | edge | none
    azure_speech_key: str = ""
    azure_speech_region: str = ""
    tts_voice_en: str = "en-IN-NeerjaNeural"
    tts_voice_ta: str = "ta-IN-PallaviNeural"
    tts_voice_hi: str = "hi-IN-SwaraNeural"
    tts_rate: str = "-4%"  # slightly slower than default sounds more "concierge"

    # --- Tenancy / security ---------------------------------------------------
    default_hotel_slug: str = "aurelia-grand"
    admin_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    cors_origin_regex: str = ""  # e.g. https://.*\.vercel\.app
    rate_limit_per_minute: int = 90

    # --- Pluggable providers (frontend mirrors these) ---------------------------
    avatar_provider: str = "demo"
    voice_provider: str = "server"

    @field_validator("groq_api_key", "azure_speech_key", "azure_speech_region", "admin_api_key", mode="before")
    @classmethod
    def _sanitize_keys(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().strip("'\"")
            if v.startswith("#"):
                return ""
        return v or ""

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        # Render / Supabase hand out postgres:// or postgresql:// URLs.
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
