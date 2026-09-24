
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Guardian X API"
    app_version: str = "0.1.0"

    # ===================================================
    # DATABASE
    # ===================================================

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "guardianx"
    db_user: str = "guardianx_user"
    db_password: str

    # ===================================================
    # OPEN-METEO ELEVATION API
    # ===================================================

    elevation_api_url: str = (
        "https://api.open-meteo.com/v1/elevation"
    )

    # ===================================================
    # OPEN-METEO WEATHER API
    # ===================================================

    weather_api_url: str = (
        "https://api.open-meteo.com/v1/forecast"
    )

    # ===================================================
    # OPENSTREETMAP OVERPASS API
    # ===================================================
    #
    # Primary Overpass instance
    #

    overpass_api_url: str = (
        "https://overpass-api.de/api/interpreter"
    )

    #
    # Fallback Overpass instance
    #
    # Used when the primary Overpass API is temporarily
    # unavailable or returns a service/network error.
    #

    overpass_fallback_url: str = (
        "https://overpass.private.coffee/api/interpreter"
    )

    # ===================================================
    # ESA WORLDCOVER
    # ===================================================

    worldcover_cache_dir: str = (
        "E:/GuardianX/data/worldcover"
    )

    worldcover_base_url: str = (
        "https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
        "v200/2021/map"
    )

    # ===================================================
    # PYDANTIC SETTINGS
    # ===================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()


