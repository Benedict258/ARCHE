import os
import time
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorClient


class MemoryManager:
    """MongoDB-backed store for behavioral signals.

    Provides `update(user_token, signal)` and `retrieve_all(user_token)` used
    by the simulation engine. Accepts an injected `client` (e.g. a
    `mongomock_motor.AsyncMongoMockClient`) so tests never touch a real
    MongoDB instance.
    """

    def __init__(self, mongo_url: str | None = None, db_name: str = "arche", client: Any = None):
        # Motor's default serverSelectionTimeoutMS is 30s — far too slow for a
        # request-serving API or a readiness probe. Fail fast instead.
        self.client = client or AsyncIOMotorClient(
            mongo_url or os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            serverSelectionTimeoutMS=3000,
        )
        self.db = self.client[db_name]
        self.signals = self.db["signals"]
        self._indexes_ready = False

    async def _ensure_indexes(self) -> None:
        if self._indexes_ready:
            return
        await self.signals.create_index([("user_token", 1), ("timestamp", -1)])
        self._indexes_ready = True

    async def update(self, user_token: str, signal: Dict[str, Any]) -> None:
        await self._ensure_indexes()
        await self.signals.insert_one(
            {
                "user_token": user_token,
                "event_type": signal.get("event_type"),
                "item_token": signal.get("item_token"),
                "item_category": signal.get("item_category"),
                "session_context": signal.get("session_context") or {},
                "engagement_depth": signal.get("engagement_depth"),
                "dwell_time_seconds": signal.get("dwell_time_seconds"),
                "sequence_position": signal.get("sequence_position"),
                "timestamp": int(time.time()),
            }
        )

    async def retrieve_all(self, user_token: str) -> Dict[str, Any]:
        await self._ensure_indexes()
        cursor = self.signals.find({"user_token": user_token}).sort("timestamp", -1).limit(50)
        rows = []
        async for doc in cursor:
            doc.pop("_id", None)
            rows.append(doc)
        return {"session": rows, "is_cold_start": len(rows) == 0}
