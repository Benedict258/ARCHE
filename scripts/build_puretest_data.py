from __future__ import annotations

import csv
import html
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PURETEST = DATA / "puretest"

SOURCES = {
    "yelp": {
        "train": DATA / "yelp_processed" / "train.json",
        "test": DATA / "yelp_processed" / "test.json",
        "catalog_lookup": DATA / "yelp_raw" / "yelp_academic_dataset_business.json",
        "history_limit": 40,
        "catalog_limit": 120,
    },
    "amazon": {
        "train": DATA / "amazon_processed" / "train.json",
        "test": DATA / "amazon_processed" / "test.json",
        "catalog_lookup": DATA / "amazon_raw" / "products.jsonl",
        "history_limit": 40,
        "catalog_limit": 120,
    },
    "goodreads": {
        "train": DATA / "goodreads_processed" / "train.json",
        "test": DATA / "goodreads_processed" / "test.json",
        "catalog_lookup": DATA / "goodreads_raw" / "books.jsonl",
        "history_limit": 40,
        "catalog_limit": 120,
    },
}

STOP_SHELVES = {
    "to-read",
    "currently-reading",
    "books",
    "owned",
    "wish-list",
    "default",
    "ebook",
    "kindle",
    "read",
    "favourites",
    "favorites",
}

PRICE_BY_SOURCE = {
    "yelp": "mid",
    "amazon": "mid",
    "goodreads": "mid",
}


@dataclass
class SessionCase:
    source: str
    user_token: str
    user_history: list[dict[str, Any]]
    item: dict[str, Any]
    actual_rating: int
    actual_review: str
    relevant_items: list[str]
    context: dict[str, Any]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def safe_text(value: Any, limit: int = 280) -> str:
    text = html.unescape(str(value or "")).strip()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def slug(text: Any) -> str:
    normalized = re.sub(r"\s+", " ", str(text or "").strip().lower())
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_") or "unknown"


def normalize_category(value: Any, default: str = "general") -> str:
    if value is None:
        return default
    if isinstance(value, list):
        value = value[0] if value else default
    text = str(value).strip()
    if not text:
        return default
    text = text.split(",")[0].strip()
    text = text.replace("&", "and")
    text = text.replace("/", " ")
    text = re.sub(r"[^A-Za-z0-9\s_-]+", "", text)
    text = re.sub(r"\s+", "_", text).lower()
    return text or default


def normalize_price_tier(value: Any, default: str = "mid") -> str:
    text = str(value or "").lower()
    if any(token in text for token in ("luxury", "premium", "high")):
        return "premium"
    if any(token in text for token in ("budget", "cheap", "low")):
        return "budget"
    if any(token in text for token in ("mid", "medium", "moderate")):
        return "mid"
    return default


def yelp_item_lookup() -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    path = DATA / "yelp_raw" / "yelp_academic_dataset_business.json"
    for row in read_jsonl(path):
        business_id = str(row.get("business_id") or "").strip()
        if not business_id:
            continue
        categories = normalize_category(row.get("categories") or "restaurant")
        lookup[business_id] = {
            "item_id": f"yelp:{business_id}",
            "item_name": safe_text(row.get("name") or business_id, limit=120),
            "item_category": categories,
            "price_tier": normalize_price_tier(row.get("attributes", {}).get("RestaurantsPriceRange2") if isinstance(row.get("attributes"), dict) else None),
            "description": safe_text(row.get("address") or row.get("city") or row.get("state"), limit=180),
            "metadata": {
                "city": row.get("city"),
                "state": row.get("state"),
                "stars": row.get("stars"),
            },
        }
    return lookup


def amazon_item_lookup() -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    path = DATA / "amazon_raw" / "products.jsonl"
    for row in read_jsonl(path):
        asin = str(row.get("parent_asin") or row.get("asin") or "").strip()
        if not asin:
            continue
        main_category = normalize_category(row.get("main_category") or row.get("categories") or row.get("store") or "shopping")
        lookup[asin] = {
            "item_id": f"amazon:{asin}",
            "item_name": safe_text(row.get("title") or asin, limit=120),
            "item_category": main_category,
            "price_tier": normalize_price_tier(row.get("price"), "mid"),
            "description": safe_text(" ".join(row.get("description") or []), limit=220),
            "metadata": {
                "store": row.get("store"),
                "average_rating": row.get("average_rating"),
                "rating_number": row.get("rating_number"),
            },
        }
    return lookup


def goodreads_item_lookup() -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    path = DATA / "goodreads_raw" / "books.jsonl"
    for row in read_jsonl(path):
        book_id = str(row.get("book_id") or "").strip()
        if not book_id:
            continue
        shelves = row.get("popular_shelves") or []
        shelf_names = [str(s.get("name") or "").strip().lower() for s in shelves if isinstance(s, dict)]
        shelf_names = [name for name in shelf_names if name and name not in STOP_SHELVES]
        category = normalize_category(shelf_names[0] if shelf_names else row.get("genres") or row.get("genre") or "books", default="books")
        title = row.get("title") or row.get("book_title") or row.get("name") or book_id
        lookup[book_id] = {
            "item_id": f"goodreads:{book_id}",
            "item_name": safe_text(title, limit=120),
            "item_category": category,
            "price_tier": "mid",
            "description": safe_text(row.get("description") or "", limit=220),
            "metadata": {
                "authors": row.get("authors"),
                "average_rating": row.get("average_rating"),
                "ratings_count": row.get("ratings_count"),
            },
        }
    return lookup


def read_source_reviews(source: str, split: str) -> list[dict[str, Any]]:
    path = SOURCES[source][split]
    return read_jsonl(path)


def source_category_and_name(source: str, row: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> tuple[str, str, str, str, dict[str, Any]]:
    if source == "yelp":
        item_id = str(row.get("business_id") or "").strip()
        lookup_row = lookup.get(item_id, {})
        item_name = safe_text(row.get("name") or lookup_row.get("item_name") or item_id, limit=120)
        item_category = normalize_category(row.get("categories") or lookup_row.get("item_category") or "restaurant")
        rating = row.get("stars_x") or row.get("stars_y") or row.get("rating") or 3
        review_text = row.get("text") or row.get("review_text") or ""
        meta = {"city": row.get("city"), "state": row.get("state")}
        return f"yelp:{item_id}", item_name, item_category, safe_text(review_text), meta, int(float(rating))

    if source == "amazon":
        item_id = str(row.get("asin") or row.get("parent_asin") or "").strip()
        lookup_row = lookup.get(item_id, {})
        item_name = safe_text(row.get("title") or lookup_row.get("item_name") or item_id, limit=120)
        item_category = normalize_category(lookup_row.get("item_category") or row.get("main_category") or "shopping")
        rating = row.get("rating") or row.get("stars") or 3
        review_text = row.get("text") or row.get("review_text") or ""
        meta = {"store": lookup_row.get("metadata", {}).get("store"), "brand": lookup_row.get("metadata", {}).get("brand")}
        return f"amazon:{item_id}", item_name, item_category, safe_text(review_text), meta, int(float(rating))

    if source == "goodreads":
        item_id = str(row.get("book_id") or "").strip()
        lookup_row = lookup.get(item_id, {})
        item_name = safe_text(row.get("title") or lookup_row.get("item_name") or item_id, limit=120)
        item_category = normalize_category(lookup_row.get("item_category") or "books", default="books")
        rating = row.get("rating") or 3
        review_text = row.get("review_text") or row.get("text") or ""
        meta = {"authors": lookup_row.get("metadata", {}).get("authors")}
        return f"goodreads:{item_id}", item_name, item_category, safe_text(review_text), meta, int(float(rating))

    raise ValueError(f"Unknown source: {source}")


def build_sessions(source: str, train_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]], lookup: dict[str, dict[str, Any]], target_cases: int = 40) -> list[SessionCase]:
    train_by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    test_by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in train_rows:
        user = str(row.get("user_id") or "").strip()
        if user:
            train_by_user[user].append(row)

    for row in test_rows:
        user = str(row.get("user_id") or "").strip()
        if user:
            test_by_user[user].append(row)

    sessions: list[SessionCase] = []
    for user in sorted(test_by_user.keys()):
        if len(sessions) >= target_cases:
            break
        history_rows = train_by_user.get(user, [])
        target_rows = test_by_user.get(user, [])
        if len(history_rows) < 3 or not target_rows:
            continue

        history_rows = history_rows[-5:]
        normalized_history: list[dict[str, Any]] = []
        for row in history_rows:
            item_id, item_name, item_category, review_text, meta, rating = source_category_and_name(source, row, lookup)
            normalized_history.append(
                {
                    "item_id": item_id,
                    "item_name": item_name,
                    "category": item_category,
                    "rating": rating,
                    "review_text": review_text,
                    "price_tier": PRICE_BY_SOURCE[source],
                    **({"metadata": meta} if meta else {}),
                }
            )

        target_row = target_rows[0]
        item_id, item_name, item_category, review_text, meta, rating = source_category_and_name(source, target_row, lookup)
        context = {
            "time_bucket": "evening" if source != "goodreads" else "afternoon",
            "region_tier": "urban",
            "entry_point": source,
        }

        sessions.append(
            SessionCase(
                source=source,
                user_token=f"puretest_{source}_{slug(user)[:24]}",
                user_history=normalized_history,
                item={
                    "name": item_name,
                    "category": item_category,
                    "price_tier": PRICE_BY_SOURCE[source],
                    "attributes": meta,
                    "item_id": item_id,
                },
                actual_rating=rating,
                actual_review=review_text,
                relevant_items=[item_id],
                context=context,
            )
        )

    return sessions


def catalog_from_sessions_and_lookup(source: str, lookup: dict[str, dict[str, Any]], used_item_ids: set[str], limit: int) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item_id in sorted(used_item_ids):
        row = lookup.get(item_id.split(":", 1)[-1], {})
        catalog.append({
            "key": item_id,
            "item_id": item_id,
            "item_name": row.get("item_name") or item_id,
            "item_category": row.get("item_category") or "general",
            "source": source,
            "description": row.get("description") or "",
            "price_tier": row.get("price_tier") or "mid",
            "metadata": row.get("metadata") or {},
        })
        seen.add(item_id)

    for raw_id, row in sorted(lookup.items(), key=lambda x: x[0]):
        item_id = row["item_id"]
        if item_id in seen:
            continue
        catalog.append({
            "key": item_id,
            "item_id": item_id,
            "item_name": row.get("item_name") or item_id,
            "item_category": row.get("item_category") or "general",
            "source": source,
            "description": row.get("description") or "",
            "price_tier": row.get("price_tier") or "mid",
            "metadata": row.get("metadata") or {},
        })
        seen.add(item_id)
        if len([c for c in catalog if c["source"] == source]) >= limit:
            break

    return catalog


def main() -> int:
    PURETEST.mkdir(parents=True, exist_ok=True)

    catalog_rows: list[dict[str, Any]] = []
    task_a_cases: list[dict[str, Any]] = []
    task_b_cases: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}

    lookups = {
        "yelp": yelp_item_lookup(),
        "amazon": amazon_item_lookup(),
        "goodreads": goodreads_item_lookup(),
    }

    used_catalog_ids: dict[str, set[str]] = {name: set() for name in SOURCES}

    for source, cfg in SOURCES.items():
        train_rows = read_source_reviews(source, "train")
        test_rows = read_source_reviews(source, "test")
        sessions = build_sessions(source, train_rows, test_rows, lookups[source], target_cases=40)

        for session in sessions:
            task_a_cases.append(
                {
                    "source": session.source,
                    "user_token": session.user_token,
                    "user_history": session.user_history,
                    "item": session.item,
                    "context": session.context,
                    "actual_rating": session.actual_rating,
                    "actual_review": session.actual_review,
                }
            )
            task_b_cases.append(
                {
                    "source": session.source,
                    "user_token": session.user_token,
                    "user_persona": {
                        "user_id": session.user_token,
                        "review_history": session.user_history,
                    },
                    "context": session.context,
                    "relevant_items": session.relevant_items,
                    "ground_truth": session.relevant_items,
                }
            )
            used_catalog_ids[source].add(session.item["item_id"])

        source_counts[source] = len(sessions)

    for source, cfg in SOURCES.items():
        catalog_rows.extend(catalog_from_sessions_and_lookup(source, lookups[source], used_catalog_ids[source], limit=cfg["catalog_limit"]))

    # Deduplicate catalog and keep order stable.
    seen: set[str] = set()
    deduped_catalog: list[dict[str, Any]] = []
    for row in catalog_rows:
        key = row["item_id"]
        if key in seen:
            continue
        seen.add(key)
        deduped_catalog.append(row)

    manifest = {
        "name": "puretest",
        "description": "Curated small cross-dataset benchmark pack built from Yelp, Amazon, and Goodreads.",
        "sources": list(SOURCES.keys()),
        "catalog_count": len(deduped_catalog),
        "task_a_cases": len(task_a_cases),
        "task_b_cases": len(task_b_cases),
        "per_source_cases": source_counts,
        "per_source_catalog_limit": {k: v["catalog_limit"] for k, v in SOURCES.items()},
        "created_by": "scripts/build_puretest_data.py",
    }

    write_jsonl(PURETEST / "catalog.jsonl", deduped_catalog)
    write_jsonl(PURETEST / "task_a_cases.jsonl", task_a_cases)
    write_jsonl(PURETEST / "task_b_cases.jsonl", task_b_cases)
    (PURETEST / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
