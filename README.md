# Klik Trader Pro (rebuilt)

Система пересобрана с нуля как стабильный стек без Telegram-зависимостей:
- FastAPI dashboard + API
- Scanner + Signal Engine
- Manual Trade Advisor
- SQLite history
- In-memory Event stream
- Backtest endpoint

## Быстрый запуск

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Открыть: `http://localhost:8000`

## .env

```env
MODE=paper
DEFAULT_SYMBOLS=BTCUSDT,ETHUSDT
DEFAULT_TIMEFRAME=15
CONFIDENCE_THRESHOLD=90
SCAN_INTERVAL_SEC=20
DASHBOARD_POLL_SEC=8
HISTORY_DB_PATH=data/trading_history.db
BYBIT_API_KEY=
BYBIT_API_SECRET=
BYBIT_TESTNET=true
```

## API
- `GET /api/snapshot`
- `GET /api/history`
- `GET /api/history/export`
- `GET /api/events`
- `POST /advisor`
- `POST /api/backtest/run`
- `POST /api/scanner/pause`
- `POST /api/scanner/resume`
- `GET /api/scanner/status`

## Pull Request workflow
```bash
git checkout -b feature/my-change
git add .
git commit -m "Describe change"
git push -u origin feature/my-change
```
Дальше на GitHub: **Compare & pull request**.
