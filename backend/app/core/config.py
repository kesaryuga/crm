from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "CRM"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    timezone: str = "Europe/Minsk"

    secret_key: str = "CHANGE_ME"
    session_cookie_name: str = "crm_session"

    database_url: str = "postgresql+psycopg://crm:CHANGE_ME@localhost:5432/crm"

    storage_backend: str = "local"
    storage_local_path: str = "/data/uploads"

    s3_endpoint: str = ""
    s3_region: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_use_ssl: bool = True

    libreoffice_path: str = "libreoffice"
    document_temp_path: str = "/tmp/crm-documents"
    max_upload_mb: int = 25
    log_level: str = "INFO"

    admin_email: str = "admin@kit-lab.by"
    admin_password: str = "ChangeMe!2026"
    login_rate_limit_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
