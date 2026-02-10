from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import settings
from app.models import Signal


class HistoryStore:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or settings.history_db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signal_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    tp1 REAL NOT NULL,
                    tp2 REAL NOT NULL,
                    tp3 REAL NOT NULL,
                    rr REAL NOT NULL,
                    confidence REAL NOT NULL,
                    why TEXT NOT NULL,
                    meta_json TEXT NOT NULL
                )
                """
            )

    def save_signal(self, signal: Signal, meta: dict[str, Any] | None = None) -> None:
        payload = asdict(signal)
        meta_json = json.dumps(meta or {}, ensure_ascii=False)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO signal_history (created_at,symbol,direction,entry,stop_loss,tp1,tp2,tp3,rr,confidence,why,meta_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    signal.created_at.isoformat(),
                    payload["symbol"],
                    payload["direction"],
                    payload["entry"],
                    payload["stop_loss"],
                    payload["tp1"],
                    payload["tp2"],
                    payload["tp3"],
                    payload["rr"],
                    payload["confidence"],
                    payload["why"],
                    meta_json,
                ),
            )

    def fetch_signals(self, symbol: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT created_at,symbol,direction,entry,stop_loss,tp1,tp2,tp3,rr,confidence,why,meta_json FROM signal_history"
        params: list[Any] = []
        if symbol:
            query += " WHERE symbol = ?"
            params.append(symbol)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            items.append(
                {
                    "created_at": row[0],
                    "symbol": row[1],
                    "direction": row[2],
                    "entry": row[3],
                    "stop_loss": row[4],
                    "tp1": row[5],
                    "tp2": row[6],
                    "tp3": row[7],
                    "rr": row[8],
                    "confidence": row[9],
                    "why": row[10],
                    "meta": json.loads(row[11] or "{}"),
                }
            )
        return items

    def stats(self) -> dict[str, float]:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM signal_history").fetchone()[0]
            avg_conf = conn.execute("SELECT COALESCE(AVG(confidence),0) FROM signal_history").fetchone()[0]
            last_24 = conn.execute(
                "SELECT COUNT(*) FROM signal_history WHERE created_at >= ?",
                ((datetime.utcnow() - timedelta(days=1)).isoformat(),),
            ).fetchone()[0]
        return {"total_signals": float(total), "avg_confidence": float(avg_conf), "signals_last_24h": float(last_24)}
