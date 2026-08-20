"""Fetch a small, real slice of Amazon Reviews 2023 for ARCHE's data pipeline.

Streams from Hugging Face (McAuley-Lab/Amazon-Reviews-2023) so this pulls only
the first N rows of one category's reviews and product metadata instead of a
multi-GB download.

Not a runtime dependency of the API — this is a one-time/occasional data-prep
tool. Requires (this dataset still uses a Hub loading script, so `datasets`
must be pinned below the version that dropped script support):

    pip install "datasets==2.19.2" huggingface_hub

Usage:
    python scripts/fetch_real_dataset.py --category Video_Games
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _stream(config_name: str):
    from datasets import load_dataset

    return load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        config_name,
        split="full",
        streaming=True,
        trust_remote_code=True,
    )


def fetch_reviews(category: str, limit: int, out_path: Path) -> int:
    ds = _stream(f"raw_review_{category}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as handle:
        for row in ds:
            if count >= limit:
                break
            asin = row.get("parent_asin") or row.get("asin")
            user_id = row.get("user_id")
            rating = row.get("rating")
            if not asin or not user_id or rating is None:
                continue
            timestamp_ms = row.get("timestamp")
            record = {
                "reviewerID": user_id,
                "asin": asin,
                "overall": rating,
                "reviewText": row.get("text") or "",
                "summary": row.get("title") or "",
                "unixReviewTime": int(timestamp_ms / 1000) if timestamp_ms else None,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def fetch_products(category: str, limit: int, out_path: Path) -> int:
    ds = _stream(f"raw_meta_{category}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as handle:
        for row in ds:
            if count >= limit:
                break
            asin = row.get("parent_asin")
            title = row.get("title")
            if not asin or not title:
                continue
            record = {
                "parent_asin": asin,
                "title": title,
                "main_category": row.get("main_category") or category,
                "categories": row.get("categories") or [category],
                "price": row.get("price"),
                "description": row.get("description") or [],
                "store": row.get("store"),
                "average_rating": row.get("average_rating"),
                "rating_number": row.get("rating_number"),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", default="Video_Games", help="Amazon Reviews 2023 category name")
    parser.add_argument("--review-limit", type=int, default=4000)
    parser.add_argument("--product-limit", type=int, default=2000)
    args = parser.parse_args()

    raw_dir = ROOT / "data" / "amazon_raw"
    reviews_written = fetch_reviews(args.category, args.review_limit, raw_dir / "reviews.jsonl")
    products_written = fetch_products(args.category, args.product_limit, raw_dir / "products.jsonl")

    summary = {"category": args.category, "reviews_written": reviews_written, "products_written": products_written}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
