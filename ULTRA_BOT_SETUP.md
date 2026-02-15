# Ultra Python Bot (без JS/дашборда)

## Что умеет
- Чистый Python бот (`ultra_bot.py`) для Ubuntu.
- Мульти-таймфрейм анализ: **5m + 1h + 4h + 1d**.
- Сильный сигнал по совокупности индикаторов (EMA/RSI/MACD/ADX/ATR/Stoch/CCI/Bollinger/объёмы).
- Доп. анализ рынка: **стакан (ликвидность/дисбаланс/спред)** + **индекс страха и жадности** + **уровни Fibonacci**.
- Шлёт Telegram-уведомление **только когда confidence >= 90%** (или твой порог).
- В уведомлении сразу есть:
  - направление (LONG/SHORT)
  - цена входа
  - **Stop Loss**
  - **Take Profit**
  - разбор по каждому ТФ.

## Установка на Ubuntu
```bash
cd /workspace/klik-trader
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.ultra.example .env
# заполни TELEGRAM_TOKEN и TELEGRAM_CHAT_ID
python ultra_bot.py
```

Бот автоматически читает `.env` из текущей директории (переменные экспортировать в shell не обязательно).

Если токен Telegram неверный, бот завершится с понятной ошибкой `Invalid TELEGRAM_TOKEN` (без бесконечного traceback-цикла).

## Systemd (чтобы работал 24/7)
Создай `/etc/systemd/system/ultra-bot.service`:
```ini
[Unit]
Description=Ultra Multi-Timeframe Trading Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/workspace/klik-trader
EnvironmentFile=/workspace/klik-trader/.env
ExecStart=/workspace/klik-trader/.venv/bin/python /workspace/klik-trader/ultra_bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ultra-bot
sudo systemctl start ultra-bot
sudo systemctl status ultra-bot
```

## Telegram-команды
- `/status` — полный анализ: вероятность успеха, когда входить, рекомендации, стакан, Fear&Greed, Fibonacci и метрики по ТФ.
- `/stats` — статистика в процентах: LONG/SHORT и % индикаторов за 1 день / 7 дней / 30 дней + частота алертов.
- `/sdel <summa_usdt> [risk_%]` — расчёт сделки: куда ставить SL/TP, размер позиции и потенц. прибыль.
  - Пример: `/sdel 1000 1.5`


В сообщениях бот показывает понятные поля на русском: **Вероятность успеха**, **Когда входить**, и блок **Рекомендации**.


Можно переопределить источник индекса страха/жадности через `FEAR_GREED_API_URL` в `.env`.
