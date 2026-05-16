import json
import time
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict

from .local_vector_store import LocalVectorStore


class MemoryManager:
    """Minimal MemoryManager using sqlite for metadata and LocalVectorStore for vectors.

    Provides `update(user_token, signal)` and `retrieve_all(user_token)` used by
    the simulation engine prototype.
    """

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._lock = threading.Lock()
        self._ensure_tables()
        self.vector_store = LocalVectorStore()

    def _ensure_tables(self) -> None:
        with self._lock:
            c = self.conn.cursor()
            c.execute(
            """
        CREATE TABLE IF NOT EXISTS signals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_token TEXT,
            event_type TEXT,
            item_token TEXT,
            item_category TEXT,
            session_context TEXT,
            engagement_depth REAL,
            dwell_time_seconds INTEGER,
            sequence_position INTEGER,
            timestamp INTEGER
        )
        """
            )
            self.conn.commit()

    def update(self, user_token: str, signal: Dict[str, Any]) -> None:
        with self._lock:
            c = self.conn.cursor()
            c.execute(
            """
        INSERT INTO signals(user_token,event_type,item_token,item_category,session_context,engagement_depth,dwell_time_seconds,sequence_position,timestamp)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
            (
                user_token,
                signal.get("event_type"),
                signal.get("item_token"),
                signal.get("item_category"),
                json.dumps(signal.get("session_context") or {}),
                signal.get("engagement_depth"),
                signal.get("dwell_time_seconds"),
                signal.get("sequence_position"),
                int(time.time()),
            ),
            )
            self.conn.commit()
        # persist minimal vector/key mapping for demo purposes
        key = f"{user_token}:{signal.get('item_token') or ''}"
        self.vector_store.add(key, [0.0], {"item_category": signal.get("item_category")})

    def retrieve_all(self, user_token: str) -> Dict[str, Any]:
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM signals WHERE user_token=? ORDER BY id DESC LIMIT 50", (user_token,))
            rows = c.fetchall()
        is_cold = len(rows) == 0
        return {"session": rows, "is_cold_start": is_cold}
