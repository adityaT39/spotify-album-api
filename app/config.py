"""Application configuration, loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Album Rating API"

    # Database. Defaults to a local SQLite file so the app runs with zero setup.
    # Swap this for a PostgreSQL URL later without changing any other code.
    database_url: str = "sqlite:///./albums.db"

    # Spotify OAuth credentials. Create an app at
    # https://developer.spotify.com/dashboard and fill these into your .env file.
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8000/auth/spotify/callback"

    # Secret used to sign our own JWT session tokens. Override in production.
    jwt_secret: str = "dev-secret-change-me"
    jwt_expires_minutes: int = 60 * 24 * 7  # one week

    # Redis, used to cache Spotify catalog lookups.
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
