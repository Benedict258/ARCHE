"""Item-item collaborative filtering, computed offline from real review data.

This replaces the `collaborative_score` signal that `score_item_against_simulation`
(agents/recommendation_scoring.py) has always accepted but nothing ever
actually populated with a real value (live-search items got a hardcoded
`1.0`; catalog items got nothing). Standard item-based CF: two items are
similar when the same users rated both highly, weighted by cosine similarity
over their "liked" user sets so popular items don't dominate purely on
volume.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


class CollaborativeFilteringIndex:
    def __init__(self, min_rating: float = 4.0) -> None:
        self.min_rating = min_rating
        self._item_users: dict[str, set[str]] = {}
        self._similarity_cache: dict[str, list[tuple[str, float]]] = {}
        self._built = False

    def available(self) -> bool:
        return self._built and bool(self._item_users)

    def build_from_processed_reviews(self, *paths: Path) -> None:
        """Build the index from one or more `data/<source>_processed/train.json`
        files (JSONL: one review per line, with a `user_id` field and a
        source-specific item id + rating field)."""
        liked: dict[str, set[str]] = defaultdict(set)

        for path in paths:
            source = self._source_from_path(path)
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    item_key = self._item_key(source, row)
                    user_id = row.get("user_id")
                    rating = row.get("overall") or row.get("rating") or row.get("stars")
                    if not item_key or not user_id or rating is None:
                        continue
                    if float(rating) >= self.min_rating:
                        liked[item_key].add(str(user_id))

        self._item_users = dict(liked)
        self._similarity_cache = {}
        self._built = True

    @staticmethod
    def _source_from_path(path: Path) -> str:
        name = path.parent.name
        return name.split("_processed")[0]

    @staticmethod
    def _item_key(source: str, row: dict[str, Any]) -> str | None:
        if source == "amazon":
            asin = row.get("asin") or row.get("parent_asin")
            return f"amazon:{asin}" if asin else None
        if source == "yelp":
            business_id = row.get("business_id")
            return f"yelp:{business_id}" if business_id else None
        if source == "goodreads":
            book_id = row.get("book_id")
            return f"goodreads:{book_id}" if book_id else None
        return None

    def similar_items(self, item_key: str, top_k: int = 20) -> list[tuple[str, float]]:
        if item_key in self._similarity_cache:
            return self._similarity_cache[item_key][:top_k]

        target_users = self._item_users.get(item_key)
        if not target_users:
            return []

        scored: list[tuple[str, float]] = []
        for other_key, other_users in self._item_users.items():
            if other_key == item_key:
                continue
            overlap = len(target_users & other_users)
            if not overlap:
                continue
            denom = math.sqrt(len(target_users) * len(other_users))
            score = overlap / denom if denom else 0.0
            if score > 0:
                scored.append((other_key, score))

        scored.sort(key=lambda pair: pair[1], reverse=True)
        self._similarity_cache[item_key] = scored
        return scored[:top_k]


_default_index: CollaborativeFilteringIndex | None = None


def get_default_index() -> CollaborativeFilteringIndex:
    """Lazily builds a process-wide index from whatever processed splits exist."""
    global _default_index
    if _default_index is None:
        _default_index = CollaborativeFilteringIndex()
        root = Path("data")
        _default_index.build_from_processed_reviews(
            root / "amazon_processed" / "train.json",
            root / "yelp_processed" / "train.json",
            root / "goodreads_processed" / "train.json",
        )
    return _default_index
