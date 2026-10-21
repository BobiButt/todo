# ============================================================================
# FILE:       backend/app/config.py
# PURPOSE:    Load all runtime configuration from the .env file (and real
#             environment variables) into ONE typed, validated object, so no
#             other module ever reads os.environ or hard-codes a secret.
# HOW IT WORKS: pydantic-settings' BaseSettings maps each KEY=VALUE from .env
#             onto an annotated Python field. Types are coerced ("2097152" ->
#             int), wrong types raise a clear error at startup, and a module-
#             level `settings` object is created once (singleton) at import.
# USED BY / DEPENDS ON: reads backend/.env; imported by database.py, main.py,
#             alembic/env.py, services/*.
# KEY CONCEPTS: environment variables, settings object (12-factor app),
#             JSON-encoded lists in .env, import-time singleton.
# ============================================================================

"""Typed application settings loaded from .env via pydantic-settings."""

# BaseSettings is the pydantic-settings class that merges OS environment
# variables with a .env file — OS env wins, so CI/containers can override.
from pydantic_settings import BaseSettings, SettingsConfigDict

# field_validator lets us normalize raw values (the CORS list arrives as text)
from pydantic import field_validator


class Settings(BaseSettings):
    """Application configuration with one field per .env key.

    Parameters (all optional — sensible development defaults are provided):
        environment (str): "development" or "production"; controls docs/debug.
        database_url (str): SQLAlchemy async PostgreSQL connection string.
        cors_origins (list[str]): browser origins allowed by CORS.
        app_prefix (str): prefix mounted before every API router (/api/v1).
        max_import_bytes (int): hard cap for uploaded import files (2 MB).

    Raises:
        pydantic.ValidationError: on startup if a .env value has a wrong type.

    Example:
        >>> settings.is_development
        True
    """

    # "development" keeps /docs (Swagger UI) reachable; "production" hides it.
    environment: str = "development"

    # Async SQLAlchemy URL: postgresql+asyncpg://user:pass@host:port/dbname.
    # A default exists so importing the module never explodes before .env is
    # copied — but real work must use the password from POSTGRES_SETUP.md §5.
    database_url: str = (
        "postgresql+asyncpg://taskflow_user:CHANGE_ME_strong_password"
        "@localhost:5432/taskflow"
    )

    test_database_url: str = (
        "postgresql+asyncpg://taskflow_user:CHANGE_ME_strong_password"
        "@localhost:5432/taskflow_test"
    )

    # Allowed browser origins. Default = Vite's dev server port.
    cors_origins: list[str] = ["http://localhost:5173"]

    # Every router is mounted under this path (versioned API, see main.py).
    app_prefix: str = "/api/v1"

    # 2 MiB = 2,097,152 bytes. Uploads above this receive HTTP 413.
    max_import_bytes: int = 2_097_152

    # --- JWT authentication ---
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # --- SMTP / email OTP ---
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"
    otp_expire_minutes: int = 10

    # --- Google OAuth ---
    google_client_id: str = ""
    google_client_secret: str = ""

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # model_config tells pydantic-settings where to look for the .env file and
    # to ignore unknown keys (so a stray line in .env never crashes startup).
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,  # database_url == DATABASE_URL for lookup
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: object) -> object:
        """Accept CORS_ORIGINS as a list, JSON text, or comma-separated text.

        .env files store everything as text, so the value often arrives as
        '["http://localhost:5173"]'. pydantic-settings already decodes JSON
        for complex fields; this validator adds a plain comma-separated
        fallback like "http://a, http://b".

        Parameters:
            value: raw value read from the environment (str | list | None).

        Returns:
            list[str] (or the value untouched when already correct).

        Raises:
            ValueError: never — unparseable input falls through to pydantic's
            own type validation, which produces the friendly error report.
        """
        # Already a list (e.g. hard-coded default) -> nothing to do.
        if isinstance(value, list):
            return value
        # A comma-separated string without brackets -> split on commas.
        if isinstance(value, str) and not value.strip().startswith("["):
            return [part.strip() for part in value.split(",") if part.strip()]
        # Anything else (JSON text) -> let pydantic parse it normally.
        return value

    @property
    def is_development(self) -> bool:
        """bool: True when running locally (enables Swagger UI and debug).

        Usage:
            if settings.is_development:
                print("Docs at /docs")
        """
        # Comparison is case-insensitive so "Development" also works.
        return self.environment.lower() in {"development", "dev", "local"}

    @property
    def is_production(self) -> bool:
        """bool: True when the environment is explicitly "production"."""
        return self.environment.lower() == "production"


# `settings` is the single configuration object imported everywhere:
#     from app.config import settings
# It is built the moment this module is first imported (import-time singleton).
settings = Settings()
