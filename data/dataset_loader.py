from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .amazon_pipeline import AmazonPipeline
from .goodreads_pipeline import GoodreadsPipeline
from .yelp_pipeline import YelpPipeline


@dataclass
class DatasetItem:
    key: str
    item_name: str
    item_category: str
    source: str
    description: str = ""
    price_tier: str = "mid"
    metadata: dict[str, Any] = field(default_factory=dict)


class UnifiedDatasetLoader:
    """Loads and normalizes real dataset assets for retrieval and evaluation.

    The loader prefers processed splits when available, then falls back to raw
    source files. It is intentionally permissive so the hackathon MVP can run
    without the datasets being present, while automatically switching to real
    data when it is available in the workspace.
    """

    def __init__(self, root_dir: str = "data"):
        self.root_dir = Path(root_dir)
        self.yelp = YelpPipeline(raw_dir=self.root_dir / "yelp_raw", processed_dir=self.root_dir / "yelp_processed")
        self.amazon = AmazonPipeline(raw_dir=self.root_dir / "amazon_raw", processed_dir=self.root_dir / "amazon_processed")
        self.goodreads = GoodreadsPipeline(raw_dir=self.root_dir / "goodreads_raw", processed_dir=self.root_dir / "goodreads_processed")

    @staticmethod
    def _read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for idx, line in enumerate(handle):
                if limit is not None and idx >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    @staticmethod
    def _read_csv(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for idx, row in enumerate(reader):
                if limit is not None and idx >= limit:
                    break
                rows.append(dict(row))
        return rows

    @staticmethod
    def _normalize_price_tier(value: Any) -> str:
        text = str(value or "").lower()
        if any(token in text for token in ("luxury", "premium", "high")):
            return "premium"
        if any(token in text for token in ("budget", "cheap", "low")):
            return "budget"
        if any(token in text for token in ("mid", "medium", "moderate")):
            return "mid"
        return "mid"

    @staticmethod
    def _slug(text: Any) -> str:
        normalized = " ".join(str(text or "").strip().lower().split())
        return normalized.replace(" ", "_") or "unknown"

    def _catalog_from_yelp(self, limit: int) -> list[DatasetItem]:
        candidates: list[DatasetItem] = []
        processed_train = self.root_dir / "yelp_processed" / "train.json"
        processed_source = self._read_jsonl(processed_train, limit=limit)
        if processed_source:
            for row in processed_source:
                name = row.get("name") or row.get("business_name") or row.get("item_name") or "yelp_item"
                categories = row.get("categories") or row.get("item_category") or row.get("category") or "restaurant"
                candidates.append(
                    DatasetItem(
                        key=f"yelp:{row.get('business_id') or row.get('item_id') or self._slug(name)}",
                        item_name=str(name),
                        item_category=str(categories).split(",")[0].strip() or "restaurant",
                        source="yelp",
                        description=str(row.get("text") or row.get("review_text") or ""),
                        price_tier=self._normalize_price_tier(row.get("price_tier") or row.get("attributes", {}).get("RestaurantsPriceRange2") if isinstance(row.get("attributes"), dict) else None),
                        metadata={"city": row.get("city"), "state": row.get("state"), "stars": row.get("stars")},
                    )
                )
        else:
            raw_businesses = self._read_jsonl(self.root_dir / "yelp_raw" / "yelp_academic_dataset_business.json", limit=limit)
            for row in raw_businesses:
                name = row.get("name") or "yelp_business"
                categories = row.get("categories") or "restaurant"
                candidates.append(
                    DatasetItem(
                        key=f"yelp:{row.get('business_id') or self._slug(name)}",
                        item_name=str(name),
                        item_category=str(categories).split(",")[0].strip() or "restaurant",
                        source="yelp",
                        description=str(row.get("address") or ""),
                        price_tier=self._normalize_price_tier(row.get("attributes", {}).get("RestaurantsPriceRange2") if isinstance(row.get("attributes"), dict) else None),
                        metadata={"city": row.get("city"), "state": row.get("state"), "stars": row.get("stars")},
                    )
                )
        return candidates[:limit]

    def _catalog_from_amazon(self, limit: int) -> list[DatasetItem]:
        candidates: list[DatasetItem] = []
        products = self._read_jsonl(self.root_dir / "amazon_raw" / "products.jsonl", limit=limit)
        if products:
            source_rows = products
        else:
            reviews = self._read_jsonl(self.root_dir / "amazon_raw" / "reviews.jsonl", limit=limit)
            source_rows = reviews
        for row in source_rows:
            name = row.get("title") or row.get("productTitle") or row.get("product_name") or row.get("asin") or "amazon_item"
            category = row.get("category") or row.get("categories") or row.get("main_cat") or "shopping"
            candidates.append(
                DatasetItem(
                    key=f"amazon:{row.get('asin') or row.get('product_id') or self._slug(name)}",
                    item_name=str(name),
                    item_category=str(category).split(",")[0].strip() or "shopping",
                    source="amazon",
                    description=str(row.get("description") or row.get("reviewText") or ""),
                    price_tier=self._normalize_price_tier(row.get("price") or row.get("price_tier")),
                    metadata={"brand": row.get("brand"), "overall": row.get("overall")},
                )
            )
        return candidates[:limit]

    def _catalog_from_goodreads(self, limit: int) -> list[DatasetItem]:
        candidates: list[DatasetItem] = []
        books = self._read_jsonl(self.root_dir / "goodreads_raw" / "books.jsonl", limit=limit)
        if not books:
            books = self._read_csv(self.root_dir / "goodreads_raw" / "books.csv", limit=limit)
        source_rows = books or self._read_jsonl(self.root_dir / "goodreads_raw" / "reviews.jsonl", limit=limit)
        for row in source_rows:
            name = row.get("title") or row.get("book_title") or row.get("name") or "goodreads_item"
            category = row.get("genre") or row.get("category") or row.get("genres") or "books"
            candidates.append(
                DatasetItem(
                    key=f"goodreads:{row.get('book_id') or row.get('isbn') or self._slug(name)}",
                    item_name=str(name),
                    item_category=str(category).split(",")[0].strip() or "books",
                    source="goodreads",
                    description=str(row.get("description") or row.get("review_text") or ""),
                    price_tier="mid",
                    metadata={"authors": row.get("authors"), "rating": row.get("rating")},
                )
            )
        return candidates[:limit]

    def load_catalog(self, limit_per_source: int = 200) -> list[dict[str, Any]]:
        items: list[DatasetItem] = []
        items.extend(self._catalog_from_yelp(limit_per_source))
        items.extend(self._catalog_from_amazon(limit_per_source))
        items.extend(self._catalog_from_goodreads(limit_per_source))

        deduped: dict[str, DatasetItem] = {}
        for item in items:
            deduped[item.key] = item

        return [
            {
                "key": item.key,
                "item_name": item.item_name,
                "item_category": item.item_category,
                "source": item.source,
                "description": item.description,
                "price_tier": item.price_tier,
                "metadata": item.metadata,
            }
            for item in deduped.values()
        ]

    def has_real_datasets(self) -> bool:
        return bool(
            list(self.root_dir.glob("yelp_raw/*"))
            or list(self.root_dir.glob("yelp_processed/*"))
            or list(self.root_dir.glob("amazon_raw/*"))
            or list(self.root_dir.glob("amazon_processed/*"))
            or list(self.root_dir.glob("goodreads_raw/*"))
            or list(self.root_dir.glob("goodreads_processed/*"))
        )

    def load_yelp_catalog(self, limit: int = 100) -> list[dict[str, Any]]:
        """Load Yelp restaurant/business catalog for recommendations."""
        items = self._catalog_from_yelp(limit)
        return [
            {
                "key": item.key,
                "item_name": item.item_name,
                "item_category": item.item_category,
                "source": item.source,
                "description": item.description,
                "price_tier": item.price_tier,
                "metadata": item.metadata,
            }
            for item in items
        ]

    def seed_vector_store(self, vector_store, limit_per_source: int = 200) -> int:
        catalog = self.load_catalog(limit_per_source=limit_per_source)
        count = 0
        for item in catalog:
            text = f"{item['item_name']} | {item['item_category']} | {item.get('source', '')}"
            from agents.retrieval_agent import RetrievalAgent

            vector_store.add(
                item["key"],
                RetrievalAgent.text_to_vector(text),
                {
                    "item_name": item["item_name"],
                    "item_category": item["item_category"],
                    "source": item["source"],
                    "price_tier": item.get("price_tier", "mid"),
                    "description": item.get("description", ""),
                    **(item.get("metadata") or {}),
                },
            )
            count += 1
        return count
