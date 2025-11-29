from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Database
    postgres_user: str = Field(..., validation_alias="POSTGRES_USER")
    postgres_password: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., validation_alias="POSTGRES_DB")
    postgres_host: str = Field("localhost", validation_alias="POSTGRES_HOST")
    postgres_port: str = Field("5432", validation_alias="POSTGRES_PORT")

    # Celery / Lichess (optional - only needed for Celery services)
    lichess_username: str = Field("", validation_alias="LICHESS_USERNAME")
    lichess_token: str = Field("", validation_alias="LICHESS_TOKEN")
    fastapi_route: str = Field("", validation_alias="FASTAPI_ROUTE")
    celery_broker_url: str = Field("", validation_alias="CELERY_BROKER_URL")

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()
