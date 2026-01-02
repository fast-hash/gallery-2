"""Application configuration for Smart Gallery.

This module centralizes settings so they can be reused across the app and
optionally overridden via environment variables. Defaults are mobile-friendly
and avoid platform-specific paths.
"""

from pathlib import Path

from pydantic import BaseSettings, Field, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration values for the application."""

    use_real_ai: bool = Field(
        False,
        alias="USE_REAL_AI",
        description="Toggle between the mock AI response and the real Ollama endpoint.",
    )
    ollama_api_url: str = Field(
        "http://localhost:11434/api/generate",
        alias="OLLAMA_API_URL",
        description=(
            "Endpoint for the Ollama server. For Android emulators, you may need "
            "to use http://10.0.2.2:11434."
        ),
    )
    system_prompt: str = Field(
        (
            "You are Joy-Caption running on-device. Given an image, return a concise "
            "description and a list of short, search-friendly tags in JSON format. "
            "Avoid personally identifiable information."
        ),
        alias="SYSTEM_PROMPT",
    )
    gallery_dir: Path = Field(
        default_factory=lambda: Path.home() / "SmartGallery" / "gallery",
        alias="GALLERY_DIR",
        description=(
            "Root folder for user-managed gallery images. The directory is created "
            "if it does not exist."
        ),
    )
    db_path: Path = Field(
        default_factory=lambda: Path.home() / "SmartGallery" / "smart_gallery.db",
        alias="DB_PATH",
        description="SQLite database file path.",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
settings.gallery_dir.mkdir(parents=True, exist_ok=True)
settings.db_path.parent.mkdir(parents=True, exist_ok=True)
