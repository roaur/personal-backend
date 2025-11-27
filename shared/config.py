from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    lichess_username: str = Field(..., validation_alias="LICHESS_USERNAME")
    lichess_token: str = Field(..., validation_alias="LICHESS_TOKEN")
    fastapi_route: str = Field(..., validation_alias="FASTAPI_ROUTE")
    
    postgres_user: str = Field(..., validation_alias="POSTGRES_USER")
    postgres_password: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., validation_alias="POSTGRES_DB")
    postgres_host: str = Field("localhost", validation_alias="POSTGRES_HOST")
    postgres_port: str = Field("5432", validation_alias="POSTGRES_PORT")

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"  # Optional: load other environment variables from a .env file
        env_file_encoding = "utf-8"
        extra = 'ignore'


    # def load_lichess_token(self):
    #     """Read the token from a secure file and assign it to `lichess_token`."""
    #     token_path = Path(".lichess.token")
    #     if token_path.is_file():
    #         self.lichess_token = token_path.read_text().strip()

# Instantiate settings and load the token
settings = Settings()
# settings.load_lichess_token()