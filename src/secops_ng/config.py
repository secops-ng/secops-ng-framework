"""Runtime configuration for SecOps-NG.

All settings are sourced from environment variables (or an optional `.env`
file). **No secret has a default value** — credentials must be injected at
runtime by the operator, via env vars, a vault sidecar, or the deployment
platform's secret manager.

See `.env.example` for the full set of recognised variables.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """SecOps-NG runtime settings.

    Non-secret operational defaults (e.g. local Temporal dev cluster) are
    fine. Anything that authenticates to a third party must remain `None`
    here and be supplied by the runtime environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Temporal ----------------------------------------------------------
    temporal_host: str = Field(default="localhost:7233")
    temporal_namespace: str = Field(default="default")
    temporal_task_queue: str = Field(default="secops-ng")

    # --- Observability -----------------------------------------------------
    log_level: LogLevel = Field(default="INFO")

    # --- Optional LLM backends (runtime-injected, never defaulted) ---------
    openai_api_key: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)

    # --- Sovereignty hints -------------------------------------------------
    # Operators can pin the framework to an EU-resident inference endpoint.
    llm_base_url: str | None = Field(default=None)
    llm_region: str | None = Field(default=None)


def get_settings() -> Settings:
    """Return a fresh Settings instance.

    Kept as a function (not a module-level singleton) so tests can override
    the environment between invocations.
    """
    return Settings()
