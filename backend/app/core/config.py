from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Anthropic API
    anthropic_api_key: str = ""

    # MET Norway — User-Agent is required by their terms of service
    met_user_agent: str = "weather_traffic/0.1"

    # Backend server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "sqlite:///./data/weather_traffic.db"

    # Frontend (used for CORS and internal links)
    public_backend_url: str = "http://localhost:8000"

    # Statens vegvesen — Datex II (HTTP Basic Auth; register at vegvesen.no)
    vegvesen_username: str = ""
    vegvesen_password: str = ""

    # Application
    data_region: str = "bergen"
    default_language: str = "en"
    log_level: str = "info"


settings = Settings()
