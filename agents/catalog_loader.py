"""
Shared catalog loader for evaluation and API.
Loads processed Yelp catalog from JSONL and caches it.
"""

import json
from pathlib import Path
from typing import Any

_CATALOG_CACHE: dict[str, Any] | None = None


def load_catalog(refresh: bool = False) -> dict[str, dict[str, Any]]:
    """
    Load catalog from processed yelp JSONL.
    Caches in memory for fast repeated access.
    Returns: dict[item_id] -> {item_id, item_name, item_category, price_tier, ...}
    """
    global _CATALOG_CACHE
    
    if _CATALOG_CACHE and not refresh:
        return _CATALOG_CACHE
    
    catalog: dict[str, dict[str, Any]] = {}
    
    # Load from train and test splits
    for split_name in ["train", "test"]:
        path = Path(f"data/yelp_processed/{split_name}.json")
        if not path.exists():
            continue
        
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                item_id = row.get("business_id") or row.get("item_id") or row.get("review_id")
                if not item_id or item_id in catalog:
                    continue
                
                # Extract primary category from comma-separated categories string
                categories_str = row.get("categories") or ""
                if isinstance(categories_str, list):
                    primary_category = categories_str[0] if categories_str else "general"
                elif isinstance(categories_str, str):
                    cats = [c.strip() for c in categories_str.split(",")]
                    primary_category = cats[0] if cats else "general"
                else:
                    primary_category = "general"
                
                # Normalize category to lowercase and replace spaces/special chars
                primary_category = primary_category.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and")
                
                # Build normalized item record
                item = {
                    "item_id": item_id,
                    "item_name": row.get("name") or row.get("business_name") or row.get("item_name") or item_id[:20],
                    "item_category": primary_category or "general",
                    "price_tier": row.get("price_tier") or "mid",
                    "avg_rating": float(row.get("stars_y") or row.get("avg_rating", 3.5)),
                    "review_count": int(row.get("review_count", 1)),
                }
                catalog[item_id] = item
    
    _CATALOG_CACHE = catalog
    return catalog


def get_catalog_list(n_items: int | None = None) -> list[dict[str, Any]]:
    """
    Get catalog as list of items (for ranking).
    Optionally limit to n_items for testing.
    """
    catalog = load_catalog()
    items = list(catalog.values())
    if n_items is not None:
        items = items[:n_items]
    return items


def get_catalog_size() -> int:
    """Get total catalog size."""
    catalog = load_catalog()
    return len(catalog)
