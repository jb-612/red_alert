from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///data/alerts.db"
    tzofar_api_url: str = "https://api.tzevaadom.co.il/alerts-history"
    oref_history_url: str = "https://www.oref.org.il/WarningMessages/History/AlertsHistory.json"
    oref_referer: str = "https://www.oref.org.il/"
    oref_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    csv_url: str = (
        "https://raw.githubusercontent.com/dleshem/israel-alerts-data/main/israel-alerts.csv"
    )
    acled_api_url: str = "https://acleddata.com/api/acled/read"
    acled_token_url: str = "https://acleddata.com/oauth/token"
    acled_username: str = ""
    acled_password: str = ""
    acled_client_id: str = "acled"
    cors_origins: list[str] = ["http://localhost:5173"]
    debug: bool = False

    model_config = {"env_prefix": "RED_ALERT_", "env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
