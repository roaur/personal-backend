from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    lichess_username: str = Field(..., env="LICHESS_USERNAME")
    lichess_token: Optional[str] = None

    class Config:
        env_file = ".env"  # Optional: load other environment variables from a .env file
        env_file_encoding = "utf-8"

    def load_lichess_token(self):
        """Read the token from a secure file and assign it to `lichess_token`."""
        token_path = Path(".lichess.token")
        if token_path.is_file():
            self.lichess_token = token_path.read_text().strip()

# Instantiate settings and load the token
settings = Settings()
settings.load_lichess_token()
