from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = Field("sqlite:///./data.db", env="DATABASE_URL")
    COINPAPRIKA_API_KEY: Optional[str] = Field(None, env="COINPAPRIKA_API_KEY")
    ETL_FAIL_AFTER_N_RECORDS: Optional[int] = Field(None, env="ETL_FAIL_AFTER_N_RECORDS")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"

settings = Settings()
