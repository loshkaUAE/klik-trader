# Klik Trader Pro

Профессиональная система: **Trade Advisor + Signal Engine + Web Dashboard** (без Telegram-бота).

## Что изменено

- Убран Telegram-бот и связанные зависимости.
- Добавлен внутренний Event Center (`/api/events`) для сигналов, ошибок и системных событий.
- Добавлен API для запуска бэктеста (`POST /api/backtest/run`).
- Добавлены API управления сканером (`POST /api/scanner/pause`, `POST /api/scanner/resume`, `GET /api/scanner/status`).
- Добавлен экспорт истории сигналов в CSV (`GET /api/history/export`).
- На дашборд добавлены кнопки: pause/resume scanner, запуск backtest и export CSV, плюс лента system events.
- Сохранились: Bybit свечи, стакан, ликвидность, 90%+ стрелки на графике, история сигналов в SQLite.

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
```

## Локальный запуск

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
# или
python app/main.py
```

Открыть: `http://localhost:8000`

## Как внести изменения через Pull Request на GitHub

1. Создать ветку:
   ```bash
   git checkout -b feature/my-change
   ```
2. Внести правки и проверить локально.
3. Закоммитить:
   ```bash
   git add .
   git commit -m "Describe your change"
   ```
4. Запушить ветку:
   ```bash
   git push -u origin feature/my-change
   ```
5. На GitHub открыть репозиторий → **Compare & pull request**.
6. Заполнить title/description, проверить diff и нажать **Create pull request**.
7. После review — **Squash and merge** (или обычный merge, по вашему процессу).

## VPS 24/7 (Ubuntu)

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv git nginx
git clone <repo> /opt/klik-trader
cd /opt/klik-trader
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`/etc/systemd/system/klik-trader.service`:

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

## API (основное)

- `GET /api/snapshot?symbol=BTCUSDT&timeframe=15` — снимок рынка для UI.
- `POST /advisor` — ручной расчёт SL/TP/Confidence.
- `GET /api/history` — история сигналов из SQLite.
- `GET /api/history/export` — CSV-экспорт истории.
- `GET /api/events` — внутренние системные события (signal/error/backtest/system).
- `POST /api/backtest/run` — быстрый бэктест по символу/таймфрейму.
- `POST /api/scanner/pause` / `POST /api/scanner/resume` — управление сканером.
- `GET /api/scanner/status` — статус фонового сканера.
