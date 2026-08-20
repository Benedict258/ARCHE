"""
Shared catalog loader for evaluation and API.

Delegates to `data.dataset_loader.UnifiedDatasetLoader`, which normalizes
Yelp/Amazon/Goodreads sources uniformly — this used to hand-parse only
`data/yelp_processed/*.json`, which meant real data from any other source
was silently invisible to the live recommendation path. Falls back to a
small hardcoded demo catalog only when no real dataset is present at all.
"""

from typing import Any

_CATALOG_CACHE: dict[str, dict[str, Any]] | None = None


def _demo_catalog() -> dict[str, dict[str, Any]]:
    demo_items = [
        {"item_id": f"demo_food_{i}", "item_name": name, "item_category": cat, "price_tier": "mid", "description": "", "avg_rating": 4.0, "review_count": 10}
        for i, (name, cat) in enumerate(
            [
                ("Suya Spot", "food"),
                ("Jollof House", "nigerian_cuisine"),
                ("Palmwine Diner", "food"),
                ("Umu Okon", "nigerian_cuisine"),
                ("Breakfast Corner", "breakfast"),
                ("Evening Eats", "food"),
                ("Fine Dine Lagos", "fine_dining"),
                ("Local Grill", "fast_food"),
                ("Cozy Cafe", "cafe"),
                ("Market Bites", "street_food"),
            ],
            start=1,
        )
    ]
    return {item["item_id"]: item for item in demo_items}


def load_catalog(refresh: bool = False, limit_per_source: int = 2000) -> dict[str, dict[str, Any]]:
    """Load the recommendation catalog from whatever real datasets are present.

    Caches in memory for fast repeated access. Returns: dict[item_id] -> item.
    """
    global _CATALOG_CACHE

    if _CATALOG_CACHE and not refresh:
        return _CATALOG_CACHE

    from data.dataset_loader import UnifiedDatasetLoader

    loader = UnifiedDatasetLoader()
    rows = loader.load_catalog(limit_per_source=limit_per_source)

    catalog: dict[str, dict[str, Any]] = {}
    for row in rows:
        item_id = row.get("key")
        if not item_id:
            continue
        catalog[item_id] = {
            "item_id": item_id,
            "item_name": row.get("item_name") or item_id,
            "item_category": row.get("item_category") or "general",
            "price_tier": row.get("price_tier") or "mid",
            "description": row.get("description") or "",
            "source": row.get("source"),
            "metadata": row.get("metadata") or {},
        }

    _CATALOG_CACHE = catalog or _demo_catalog()
    return _CATALOG_CACHE


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
