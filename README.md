# Klik Trader Pro

Профессиональная система: **Trade Advisor + Signal Engine + Telegram Bot Host + Web Dashboard**.

## Что сделано по вашему запросу

- График строится на данных Bybit (по API ключам), с fallback на synthetic данные для демо.
- Красивый UI (тёмная тема, карточки, свечной Plotly-график).
- Показ стакана (bids/asks), spread, imbalance и зон ликвидности.
- Свечные бары на графике + простое распознавание паттернов (Doji/Hammer/Shooting Star).
- При сигнале **90%+** на графике рисуется стрелка вверх/вниз.
- История сигналов сохраняется в **SQLite** (`data/trading_history.db`).
- Telegram bot host (python-telegram-bot v20.3):
  - пуш сигналов,
  - команда `/status`,
  - команда `/signals`.
- Запуск 24/7 через systemd на VPS.

## Архитектура

- `app/data/*` — Bybit candles + orderbook.
- `app/indicators/engine.py` — 30+ индикаторов.
- `app/strategy/*` — market structure + confidence engine.
- `app/risk/risk_engine.py` — ATR/liquidity SL/TP.
- `app/storage/history_store.py` — хранение истории в SQLite.
- `app/telegram/bot.py` — Telegram уведомления + bot host команды.
- `app/main.py` — FastAPI dashboard API + scanner lifecycle.
- `app/static/*`, `app/templates/*` — фронт с candlestick chart + стрелки сигналов.

## .env

```env
MODE=paper
DEFAULT_SYMBOLS=BTCUSDT,ETHUSDT
DEFAULT_TIMEFRAME=15
CONFIDENCE_THRESHOLD=90
SCAN_INTERVAL_SEC=20
DASHBOARD_POLL_SEC=8
HISTORY_DB_PATH=data/trading_history.db

BYBIT_API_KEY=...
BYBIT_API_SECRET=...
BYBIT_TESTNET=true

TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
TELEGRAM_ADMIN_USER_ID=
```

## Локальный запуск

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Открыть: `http://localhost:8000`

## VPS 24/7 (Ubuntu)

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv git nginx
git clone <repo> /opt/klik-trader
cd /opt/klik-trader
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Создать `/etc/systemd/system/klik-trader.service`:

```ini
[Unit]
Description=Klik Trader Pro
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/klik-trader
EnvironmentFile=/opt/klik-trader/.env
ExecStart=/opt/klik-trader/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable klik-trader
sudo systemctl start klik-trader
sudo systemctl status klik-trader
```

Теперь сканер и Telegram bot host работают непрерывно, а история сигналов сохраняется между рестартами.
