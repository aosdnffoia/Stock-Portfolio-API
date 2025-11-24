from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database
    database_url: str = "postgresql+asyncpg://portfolio_user:portfolio_pass@localhost:5432/portfolio_db"
    
    # JWT
    secret_key: str = "secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # ETL
    ticker_symbols: str = "AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,JPM,V,WMT"
    etl_on_startup: bool = False
    etl_schedule_enabled: bool = False
    etl_schedule_hour: int = 0
    
    # Demo user
    demo_user_email: str = "demo@example.com"
    demo_user_password: str = "demo123"
    
    # Optional API keys
    alpha_vantage_api_key: str | None = None
    
    @property
    def ticker_list(self) -> List[str]:
        """Get list of ticker symbols."""
        return [t.strip().upper() for t in self.ticker_symbols.split(",")]


settings = Settings()
