from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Klik Trader Pro"
    mode: str = "paper"  # live|paper|backtest
    default_symbols: str = "BTCUSDT,ETHUSDT"
    default_timeframe: str = "15"
    bybit_api_key: str = ""
    bybit_api_secret: str = ""
    bybit_testnet: bool = True
    telegram_token: str = ""
    telegram_chat_id: str = ""
    telegram_admin_user_id: str = ""
    confidence_threshold: float = 90.0
    risk_per_trade_pct: float = 0.5
    max_open_positions: int = 3
    scan_interval_sec: int = 20
    history_db_path: str = "data/trading_history.db"
    dashboard_poll_sec: int = 8


settings = Settings()
