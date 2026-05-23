import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Any


class Settings(BaseSettings):
    model_config = {"protected_namespaces": ()}

    # Use EVENT_MED_DATA_DIR if set, otherwise local default
    event_med_data_dir: str = "./backend/data"
    database_url: str = ""
    
    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str, info) -> str:
        if v: return v
        data_dir = os.getenv("EVENT_MED_DATA_DIR", "./backend/data")
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.abspath(os.path.join(data_dir, "event_med.db"))
        return f"sqlite:///{db_path}"

    @property
    def data_dir(self) -> str:
        d = os.getenv("EVENT_MED_DATA_DIR", self.event_med_data_dir)
        os.makedirs(d, exist_ok=True)
        return os.path.abspath(d)

    @property
    def upload_dir(self) -> str:
        u_dir = os.path.join(self.data_dir, "uploads")
        os.makedirs(u_dir, exist_ok=True)
        return u_dir

    ollama_host: str = "http://localhost:11434"
    model_primary: str = "gemma4:e2b"
    model_scale: str = "gemma4:e4b"
    # Unsloth-finetuned model for festival medicine. Empty string means "same
    # as model_primary" so the app works out-of-the-box with no .env entry.
    model_medical: str = ""
    cors_origins: Any = ["*"]

    @field_validator("model_primary", mode="before")
    @classmethod
    def load_primary_model(cls, v):
        return v or os.getenv("OLLAMA_MODEL") or "gemma4:e2b"

    @field_validator("model_scale", mode="before")
    @classmethod
    def load_scale_model(cls, v):
        return v or os.getenv("OLLAMA_MODEL_SCALE") or "gemma4:e4b"

    @field_validator("model_medical", mode="before")
    @classmethod
    def load_medical_model(cls, v):
        return v or os.getenv("MODEL_MEDICAL") or ""

    @property
    def effective_medical_model(self) -> str:
        """Unsloth fine-tune when installed, vanilla primary otherwise."""
        return self.model_medical or self.model_primary

    # When True, all LLM calls go to Google AI Studio instead of local Ollama.
    cloud_mode: bool = False
    
    # Turn this on to enable verbose debug logging to backend/data/logs/event_med_debug.log
    debug_mode: bool = True
    google_api_key: str = ""
    # We will use gemini-3-flash as default cloud model for speed and capability
    cloud_model: str = "gemini-3-flash"

    @field_validator("google_api_key", mode="before")
    @classmethod
    def load_api_key(cls, v):
        if v: return v
        secret_path = "/secrets/GOOGLE_API_KEY"
        if os.path.exists(secret_path):
            try:
                with open(secret_path, "r") as f:
                    val = f.read().strip()
                    if val:
                        return val
            except Exception:
                pass
        return v or os.getenv("GEMINI_API_KEY") or ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v == "*": return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
