# ARCHE — Dataset Pipeline Instruction
## Priority 1, Item 2 — All Three Hackathon Datasets

---

> **Context:** Task A endpoint is built and passing (20 tests total).
> Now build the data pipeline. The hackathon brief specifies three
> datasets: Yelp, Amazon Reviews, and Goodreads. Build a pipeline
> for ALL THREE — not just Yelp. Each dataset feeds both Task A
> (review simulation) and Task B (recommendation evaluation).

---

## Why All Three Datasets

The hackathon brief says:
> "Where you can get Dataset: Yelp, Amazon Reviews, and Goodreads —
> three large-scale, real-world platforms with rich behavioral and
> textual signals."

Building all three gives us:

| Advantage | Detail |
|---|---|
| **Robustness** | If one dataset produces weak ROUGE/NDCG scores, we report the best |
| **Cross-domain scoring** | Task B awards 25pts for cold-start AND cross-domain performance |
| **Demo variety** | Show restaurants (Yelp), products (Amazon), books (Goodreads) on June 10 |
| **Solution paper depth** | "We evaluated across three domains" is a stronger paper than one dataset |
| **Nigerian coverage** | Amazon has Nigerian diaspora reviews. Goodreads has African authors. |

---

## Architecture — How Datasets Plug Into ARCHE

```
ALL THREE DATASETS
      │
      ▼
┌─────────────────────────────────────┐
│     UNIFIED DATA PIPELINE           │
│  data/datasets/yelp_pipeline.py     │
│  data/datasets/amazon_pipeline.py   │
│  data/datasets/goodreads_pipeline.py│
│  data/datasets/unified_loader.py    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     UNIFIED SCHEMA (all datasets    │
│     normalized to same format)      │
│                                     │
│  user_id, item_id, item_name,       │
│  item_category, rating, review_text │
│  date, price_tier, domain           │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
   TRAIN SET      TEST SET
   (80%)          (20% held out)
        │             │
        ▼             ▼
  Task A:          Task B:
  Review           NDCG@10
  Simulation       Hit Rate
  (RMSE/ROUGE)     Evaluation
```

**Critical rule:** All three datasets normalize to the same schema.
The existing simulation engine and recommendation engine receive
the same data structure regardless of which dataset is active.
The mock_data/ files are NOT touched or replaced.

---

## File Structure To Build

```
data/
├── datasets/
│   ├── __init__.py
│   ├── unified_loader.py          ← single interface for all datasets
│   ├── yelp_pipeline.py           ← Yelp processing
│   ├── amazon_pipeline.py         ← Amazon Reviews processing
│   ├── goodreads_pipeline.py      ← Goodreads processing
│   └── nigerian_extractor.py      ← Nigerian pattern extraction (all datasets)
├── raw/
│   ├── yelp/                      ← place Yelp JSON files here
│   ├── amazon/                    ← place Amazon JSON files here
│   └── goodreads/                 ← place Goodreads JSON files here
├── processed/
│   ├── yelp/
│   │   ├── train.json
│   │   ├── test.json
│   │   └── nigerian_users.json
│   ├── amazon/
│   │   ├── train.json
│   │   ├── test.json
│   │   └── nigerian_users.json
│   └── goodreads/
│       ├── train.json
│       ├── test.json
│       └── nigerian_users.json
└── evaluation/
    ├── __init__.py
    ├── task_a_evaluator.py
    ├── task_b_evaluator.py
    └── run_evaluation.py
```

---

## The Unified Schema — Every Dataset Outputs This

```python
# Every processed record from every dataset must match this schema

{
    "user_id":       "str",          # original user ID (will be hashed)
    "user_token":    "str",          # SHA-256 hashed — privacy safe
    "item_id":       "str",          # original item ID
    "item_token":    "str",          # SHA-256 hashed
    "item_name":     "str",          # restaurant/product/book name
    "item_category": "str",          # food, electronics, fiction, etc.
    "price_tier":    "str",          # budget | mid | premium | luxury
    "rating":        int,            # 1-5 stars (normalized if needed)
    "review_text":   "str",          # the review text
    "date":          "str",          # ISO format: YYYY-MM-DD
    "domain":        "str",          # "yelp" | "amazon" | "goodreads"
    "split":         "str"           # "train" | "test"
}
```

---

## Dataset 1 — Yelp Open Dataset

**Download:** https://www.yelp.com/dataset
Free. Requires registration. Download the JSON dataset.

**Files needed:**
- `yelp_academic_dataset_review.json`
- `yelp_academic_dataset_business.json`

**Place in:** `data/raw/yelp/`

**Domain:** Restaurants, local businesses, services

**Why Yelp is primary:**
- Food/restaurant domain — closest to Nigerian daily life
- Rich review text — ideal for Task A behavioural fidelity
- Nigerian language patterns present in the dataset
- Most immediately relatable for Nigerian judges on June 10

```python
# data/datasets/yelp_pipeline.py

import pandas as pd
import json
import hashlib
from pathlib import Path
from datetime import datetime

class YelpPipeline:
    """
    Processes Yelp Open Dataset into ARCHE unified schema.
    
    Download from: https://www.yelp.com/dataset
    Place JSON files in: data/raw/yelp/
    """
    
    DOMAIN = "yelp"
    RAW_DIR = Path("data/raw/yelp")
    PROCESSED_DIR = Path("data/processed/yelp")
    MIN_REVIEWS_PER_USER = 10
    TEST_RATIO = 0.20
    MAX_RECORDS = 500_000          # cap for memory safety
    
    CATEGORY_MAP = {
        "restaurants": "food",
        "food": "food",
        "shopping": "retail",
        "beauty": "beauty",
        "health": "health",
        "nightlife": "entertainment",
        "hotels": "hospitality",
        "automotive": "automotive",
    }
    
    def __init__(self):
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    @staticmethod
    def _normalize_price(price_str: str) -> str:
        mapping = {"$": "budget", "$$": "mid",
                   "$$$": "premium", "$$$$": "luxury"}
        return mapping.get(str(price_str).strip(), "mid")
    
    def _normalize_category(self, categories: str) -> str:
        if not categories:
            return "general"
        cats_lower = categories.lower()
        for key, val in self.CATEGORY_MAP.items():
            if key in cats_lower:
                return val
        return "general"
    
    def load_reviews(self) -> pd.DataFrame:
        path = self.RAW_DIR / "yelp_academic_dataset_review.json"
        records = []
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= self.MAX_RECORDS:
                    break
                records.append(json.loads(line))
        return pd.DataFrame(records)
    
    def load_businesses(self) -> pd.DataFrame:
        path = self.RAW_DIR / "yelp_academic_dataset_business.json"
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
        return pd.DataFrame(records)
    
    def process(self) -> pd.DataFrame:
        print("[Yelp] Loading reviews...")
        reviews = self.load_reviews()
        
        print("[Yelp] Loading businesses...")
        businesses = self.load_businesses()
        
        # Merge business metadata
        reviews = reviews.merge(
            businesses[["business_id", "name", "categories", "attributes"]],
            on="business_id", how="left"
        )
        
        # Filter active users
        counts = reviews.groupby("user_id").size()
        active = counts[counts >= self.MIN_REVIEWS_PER_USER].index
        reviews = reviews[reviews["user_id"].isin(active)].copy()
        print(f"[Yelp] Active users (≥{self.MIN_REVIEWS_PER_USER} reviews): {len(active)}")
        
        # Normalize to unified schema
        reviews["user_token"]    = reviews["user_id"].apply(self._hash)
        reviews["item_token"]    = reviews["business_id"].apply(self._hash)
        reviews["item_name"]     = reviews["name"].fillna("Unknown")
        reviews["item_category"] = reviews["categories"].apply(self._normalize_category)
        reviews["price_tier"]    = reviews["attributes"].apply(
            lambda a: self._normalize_price(
                (a or {}).get("RestaurantsPriceRange2", "$")
            )
        )
        reviews["rating"]        = reviews["stars"].astype(int)
        reviews["review_text"]   = reviews["text"].fillna("")
        reviews["date"]          = pd.to_datetime(
            reviews["date"]
        ).dt.strftime("%Y-%m-%d")
        reviews["domain"]        = self.DOMAIN
        
        return reviews[[
            "user_id", "user_token", "item_id", "item_token",
            "item_name", "item_category", "price_tier",
            "rating", "review_text", "date", "domain"
        ]].rename(columns={"business_id": "item_id"})
    
    def train_test_split(self, df: pd.DataFrame):
        """Sort by date per user. Last 20% = test (held out)."""
        df_sorted = df.sort_values(["user_id", "date"])
        train_parts, test_parts = [], []
        
        for _, group in df_sorted.groupby("user_id"):
            n = len(group)
            split = max(1, int(n * (1 - self.TEST_RATIO)))
            train_parts.append(group.iloc[:split].assign(split="train"))
            test_parts.append(group.iloc[split:].assign(split="test"))
        
        train = pd.concat(train_parts)
        test = pd.concat(test_parts)
        
        train.to_json(
            self.PROCESSED_DIR / "train.json",
            orient="records", lines=True
        )
        test.to_json(
            self.PROCESSED_DIR / "test.json",
            orient="records", lines=True
        )
        
        print(f"[Yelp] Train: {len(train)} | Test: {len(test)}")
        return train, test
    
    def run(self):
        df = self.process()
        return self.train_test_split(df)
```

---

## Dataset 2 — Amazon Reviews (2023)

**Download:** https://amazon-reviews-2023.github.io
Free. No registration required.

**Recommended subset:** Download one category to start.
Best options for Nigerian context:
- `Electronics` — high engagement, global
- `Clothing_Shoes_and_Jewelry` — strong Nigerian diaspora signal
- `Home_and_Kitchen` — broad appeal

**Files needed:** `*.jsonl.gz` files from the download page

**Place in:** `data/raw/amazon/`

**Domain:** E-commerce products

**Why Amazon matters:**
- Cross-domain from Yelp — earns the 25pt cold-start/cross-domain score
- Nigerian diaspora users present in dataset
- Product recommendation is BCT's core enterprise use case
- Amazon's 1-5 star scale matches Yelp exactly — unified schema works cleanly

```python
# data/datasets/amazon_pipeline.py

import pandas as pd
import json
import gzip
import hashlib
from pathlib import Path

class AmazonPipeline:
    """
    Processes Amazon Reviews 2023 dataset into ARCHE unified schema.
    
    Download from: https://amazon-reviews-2023.github.io
    Download one or more category .jsonl.gz files.
    Place in: data/raw/amazon/
    """
    
    DOMAIN = "amazon"
    RAW_DIR = Path("data/raw/amazon")
    PROCESSED_DIR = Path("data/processed/amazon")
    MIN_REVIEWS_PER_USER = 5       # Amazon is sparser — lower threshold
    TEST_RATIO = 0.20
    MAX_RECORDS = 300_000
    
    # Amazon category → normalized category
    CATEGORY_MAP = {
        "electronics":              "electronics",
        "clothing":                 "fashion",
        "shoes":                    "fashion",
        "jewelry":                  "fashion",
        "home":                     "home_goods",
        "kitchen":                  "home_goods",
        "books":                    "books",
        "toys":                     "toys",
        "sports":                   "sports",
        "beauty":                   "beauty",
        "grocery":                  "food",
        "automotive":               "automotive",
        "tools":                    "tools",
        "office":                   "office",
    }
    
    def __init__(self):
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(str(value).encode()).hexdigest()[:16]
    
    def _normalize_category(self, category_str: str) -> str:
        if not category_str:
            return "general"
        cat_lower = str(category_str).lower()
        for key, val in self.CATEGORY_MAP.items():
            if key in cat_lower:
                return val
        return "general"
    
    @staticmethod
    def _infer_price_tier(price) -> str:
        """Infer price tier from Amazon price field."""
        try:
            p = float(str(price).replace("$", "").replace(",", ""))
            if p < 20:    return "budget"
            if p < 75:    return "mid"
            if p < 200:   return "premium"
            return "luxury"
        except (ValueError, TypeError):
            return "mid"
    
    def load_reviews(self, filename: str = None) -> pd.DataFrame:
        """
        Load Amazon review JSONL.GZ file.
        If filename not specified, loads all .jsonl.gz files in raw dir.
        """
        raw_dir = self.RAW_DIR
        files = (
            [raw_dir / filename] if filename
            else list(raw_dir.glob("*.jsonl.gz")) +
                 list(raw_dir.glob("*.jsonl"))
        )
        
        if not files:
            raise FileNotFoundError(
                f"No Amazon review files found in {raw_dir}. "
                "Download from amazon-reviews-2023.github.io"
            )
        
        records = []
        for fpath in files:
            print(f"[Amazon] Loading {fpath.name}...")
            opener = gzip.open if str(fpath).endswith(".gz") else open
            with opener(fpath, "rt", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if len(records) >= self.MAX_RECORDS:
                        break
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        return pd.DataFrame(records)
    
    def load_metadata(self) -> pd.DataFrame:
        """Load Amazon item metadata if available."""
        meta_files = list(self.RAW_DIR.glob("*meta*.jsonl.gz")) + \
                     list(self.RAW_DIR.glob("*meta*.jsonl"))
        
        if not meta_files:
            return pd.DataFrame()
        
        records = []
        with (gzip.open(meta_files[0], "rt") if
              str(meta_files[0]).endswith(".gz")
              else open(meta_files[0])) as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return pd.DataFrame(records)
    
    def process(self) -> pd.DataFrame:
        print("[Amazon] Loading reviews...")
        reviews = self.load_reviews()
        
        # Try to load metadata for item names
        metadata = self.load_metadata()
        
        # Amazon 2023 field names
        # user_id → user_id, asin → item_id, rating → rating,
        # text → review_text, timestamp → date, title → item_name
        
        if "asin" not in reviews.columns:
            raise ValueError(
                "Unexpected Amazon data format. "
                "Expected fields: user_id, asin, rating, text"
            )
        
        # Merge metadata if available
        if not metadata.empty and "asin" in metadata.columns:
            reviews = reviews.merge(
                metadata[["asin", "title", "main_category", "price"]],
                on="asin", how="left"
            )
        
        # Filter active users
        counts = reviews.groupby("user_id").size()
        active = counts[counts >= self.MIN_REVIEWS_PER_USER].index
        reviews = reviews[reviews["user_id"].isin(active)].copy()
        print(f"[Amazon] Active users: {len(active)}")
        
        # Normalize to unified schema
        reviews["user_token"]    = reviews["user_id"].apply(self._hash)
        reviews["item_token"]    = reviews["asin"].apply(self._hash)
        reviews["item_name"]     = reviews.get(
            "title", pd.Series(["Unknown Product"] * len(reviews))
        ).fillna("Unknown Product")
        reviews["item_category"] = reviews.get(
            "main_category",
            pd.Series(["general"] * len(reviews))
        ).apply(self._normalize_category)
        reviews["price_tier"]    = reviews.get(
            "price",
            pd.Series([None] * len(reviews))
        ).apply(self._infer_price_tier)
        reviews["rating"]        = pd.to_numeric(
            reviews["rating"], errors="coerce"
        ).fillna(3).astype(int).clip(1, 5)
        reviews["review_text"]   = reviews["text"].fillna("")
        reviews["date"]          = pd.to_datetime(
            reviews.get("timestamp", pd.Series([0] * len(reviews))),
            unit="ms", errors="coerce"
        ).dt.strftime("%Y-%m-%d").fillna("2020-01-01")
        reviews["domain"]        = self.DOMAIN
        reviews["item_id"]       = reviews["asin"]
        reviews["user_id"]       = reviews["user_id"]
        
        return reviews[[
            "user_id", "user_token", "item_id", "item_token",
            "item_name", "item_category", "price_tier",
            "rating", "review_text", "date", "domain"
        ]]
    
    def train_test_split(self, df: pd.DataFrame):
        """Sort by date per user. Last 20% = test (held out)."""
        df_sorted = df.sort_values(["user_id", "date"])
        train_parts, test_parts = [], []
        
        for _, group in df_sorted.groupby("user_id"):
            n = len(group)
            split = max(1, int(n * (1 - self.TEST_RATIO)))
            train_parts.append(group.iloc[:split].assign(split="train"))
            test_parts.append(group.iloc[split:].assign(split="test"))
        
        train = pd.concat(train_parts)
        test  = pd.concat(test_parts)
        
        train.to_json(
            self.PROCESSED_DIR / "train.json",
            orient="records", lines=True
        )
        test.to_json(
            self.PROCESSED_DIR / "test.json",
            orient="records", lines=True
        )
        
        print(f"[Amazon] Train: {len(train)} | Test: {len(test)}")
        return train, test
    
    def run(self):
        df = self.process()
        return self.train_test_split(df)
```

---

## Dataset 3 — Goodreads

**Download:** https://mengtingwan.github.io/data/goodreads
Free. No registration required.

**Recommended files:**
- `goodreads_reviews_spoiler_raw.json.gz` — full reviews with text
- `goodreads_books.json.gz` — book metadata

**Place in:** `data/raw/goodreads/`

**Domain:** Books, literature

**Why Goodreads matters:**
- Strong review TEXT quality — best for Task A ROUGE scores
- African authors and Nigerian literature present
- Highest word-count reviews of all three datasets — richer behavioral signal
- Cross-domain from both Yelp and Amazon — strengthens cross-domain scoring

**Note on ratings:** Goodreads uses 1-5 stars. Maps directly to unified schema.

```python
# data/datasets/goodreads_pipeline.py

import pandas as pd
import json
import gzip
import hashlib
from pathlib import Path

class GoodreadsPipeline:
    """
    Processes Goodreads dataset into ARCHE unified schema.
    
    Download from: https://mengtingwan.github.io/data/goodreads
    Files needed:
      - goodreads_reviews_spoiler_raw.json.gz  (reviews)
      - goodreads_books.json.gz                 (book metadata)
    Place in: data/raw/goodreads/
    """
    
    DOMAIN = "goodreads"
    RAW_DIR = Path("data/raw/goodreads")
    PROCESSED_DIR = Path("data/processed/goodreads")
    MIN_REVIEWS_PER_USER = 5
    TEST_RATIO = 0.20
    MAX_RECORDS = 300_000
    
    SHELF_TO_CATEGORY = {
        "fiction":       "fiction",
        "non-fiction":   "non_fiction",
        "fantasy":       "fiction",
        "romance":       "fiction",
        "mystery":       "fiction",
        "thriller":      "fiction",
        "science":       "non_fiction",
        "history":       "non_fiction",
        "biography":     "non_fiction",
        "self-help":     "non_fiction",
        "children":      "childrens",
        "young-adult":   "young_adult",
        "graphic":       "graphic_novel",
        "poetry":        "poetry",
        "african":       "african_literature",
        "nigeria":       "african_literature",
    }
    
    def __init__(self):
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(str(value).encode()).hexdigest()[:16]
    
    def _normalize_category(self, shelves) -> str:
        """Normalize Goodreads shelves to unified category."""
        if not shelves:
            return "fiction"
        
        if isinstance(shelves, list):
            shelf_text = " ".join(
                s.get("name", "") if isinstance(s, dict) else str(s)
                for s in shelves
            ).lower()
        else:
            shelf_text = str(shelves).lower()
        
        for key, val in self.SHELF_TO_CATEGORY.items():
            if key in shelf_text:
                return val
        
        return "fiction"
    
    @staticmethod
    def _infer_price_tier(format_str: str) -> str:
        """Books don't have prices — infer from format."""
        if not format_str:
            return "mid"
        fmt = str(format_str).lower()
        if "kindle" in fmt or "ebook" in fmt:
            return "budget"
        if "hardcover" in fmt:
            return "premium"
        if "paperback" in fmt:
            return "mid"
        return "mid"
    
    def load_reviews(self) -> pd.DataFrame:
        candidates = [
            "goodreads_reviews_spoiler_raw.json.gz",
            "goodreads_reviews_dedup.json.gz",
            "goodreads_reviews.json.gz",
        ]
        
        for name in candidates:
            path = self.RAW_DIR / name
            if path.exists():
                print(f"[Goodreads] Loading {name}...")
                records = []
                with gzip.open(path, "rt", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if i >= self.MAX_RECORDS:
                            break
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return pd.DataFrame(records)
        
        raise FileNotFoundError(
            f"No Goodreads review file found in {self.RAW_DIR}. "
            "Download from mengtingwan.github.io/data/goodreads"
        )
    
    def load_books(self) -> pd.DataFrame:
        path = self.RAW_DIR / "goodreads_books.json.gz"
        if not path.exists():
            return pd.DataFrame()
        
        records = []
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return pd.DataFrame(records)
    
    def process(self) -> pd.DataFrame:
        print("[Goodreads] Loading reviews...")
        reviews = self.load_reviews()
        
        print("[Goodreads] Loading book metadata...")
        books = self.load_books()
        
        # Merge book metadata
        if not books.empty and "book_id" in books.columns:
            reviews = reviews.merge(
                books[["book_id", "title", "popular_shelves",
                       "format", "authors"]],
                on="book_id", how="left"
            )
        
        # Filter active users
        counts = reviews.groupby("user_id").size()
        active = counts[counts >= self.MIN_REVIEWS_PER_USER].index
        reviews = reviews[reviews["user_id"].isin(active)].copy()
        print(f"[Goodreads] Active users: {len(active)}")
        
        # Normalize to unified schema
        reviews["user_token"]    = reviews["user_id"].apply(self._hash)
        reviews["item_token"]    = reviews["book_id"].apply(self._hash)
        reviews["item_id"]       = reviews["book_id"].astype(str)
        reviews["item_name"]     = reviews.get(
            "title", pd.Series(["Unknown Book"] * len(reviews))
        ).fillna("Unknown Book")
        reviews["item_category"] = reviews.get(
            "popular_shelves",
            pd.Series([None] * len(reviews))
        ).apply(self._normalize_category)
        reviews["price_tier"]    = reviews.get(
            "format",
            pd.Series([None] * len(reviews))
        ).apply(self._infer_price_tier)
        
        # Goodreads rating: 0 means "no rating" — treat as missing
        reviews["rating"] = pd.to_numeric(
            reviews["rating"], errors="coerce"
        ).replace(0, None).fillna(3).astype(int).clip(1, 5)
        
        reviews["review_text"] = reviews.get(
            "review_text",
            reviews.get("text", pd.Series([""] * len(reviews)))
        ).fillna("")
        
        reviews["date"] = pd.to_datetime(
            reviews.get("date_updated",
            reviews.get("read_at",
            pd.Series(["2020-01-01"] * len(reviews)))),
            errors="coerce"
        ).dt.strftime("%Y-%m-%d").fillna("2020-01-01")
        
        reviews["domain"] = self.DOMAIN
        
        return reviews[[
            "user_id", "user_token", "item_id", "item_token",
            "item_name", "item_category", "price_tier",
            "rating", "review_text", "date", "domain"
        ]]
    
    def train_test_split(self, df: pd.DataFrame):
        df_sorted = df.sort_values(["user_id", "date"])
        train_parts, test_parts = [], []
        
        for _, group in df_sorted.groupby("user_id"):
            n = len(group)
            split = max(1, int(n * (1 - self.TEST_RATIO)))
            train_parts.append(group.iloc[:split].assign(split="train"))
            test_parts.append(group.iloc[split:].assign(split="test"))
        
        train = pd.concat(train_parts)
        test  = pd.concat(test_parts)
        
        train.to_json(
            self.PROCESSED_DIR / "train.json",
            orient="records", lines=True
        )
        test.to_json(
            self.PROCESSED_DIR / "test.json",
            orient="records", lines=True
        )
        
        print(f"[Goodreads] Train: {len(train)} | Test: {len(test)}")
        return train, test
    
    def run(self):
        df = self.process()
        return self.train_test_split(df)
```

---

## The Unified Loader — Single Interface For Everything

```python
# data/datasets/unified_loader.py

from pathlib import Path
import pandas as pd
import json

class UnifiedDatasetLoader:
    """
    Single interface to load any processed dataset into ARCHE.
    
    All three pipelines output the same schema.
    Use this class everywhere in the codebase — never import
    individual pipeline classes directly in agents or API routes.
    
    Usage:
        loader = UnifiedDatasetLoader()
        train = loader.load_train("yelp")
        test  = loader.load_test("amazon")
        all_train = loader.load_all_train()
    """
    
    DATASETS = ["yelp", "amazon", "goodreads"]
    PROCESSED_BASE = Path("data/processed")
    
    def load_train(self, dataset: str) -> pd.DataFrame:
        """Load training split for a specific dataset."""
        return self._load(dataset, "train")
    
    def load_test(self, dataset: str) -> pd.DataFrame:
        """Load test split for a specific dataset."""
        return self._load(dataset, "test")
    
    def load_all_train(self) -> pd.DataFrame:
        """Load and combine training data from all available datasets."""
        frames = []
        for ds in self.DATASETS:
            path = self.PROCESSED_BASE / ds / "train.json"
            if path.exists():
                frames.append(self._load(ds, "train"))
                print(f"[Loader] Loaded {ds} training data")
            else:
                print(f"[Loader] {ds} not yet processed — skipping")
        
        if not frames:
            raise FileNotFoundError(
                "No processed datasets found. "
                "Run at least one dataset pipeline first."
            )
        
        combined = pd.concat(frames, ignore_index=True)
        print(f"[Loader] Combined training records: {len(combined)}")
        return combined
    
    def load_all_test(self) -> pd.DataFrame:
        """Load and combine test data from all available datasets."""
        frames = []
        for ds in self.DATASETS:
            path = self.PROCESSED_BASE / ds / "test.json"
            if path.exists():
                frames.append(self._load(ds, "test"))
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    def get_user_history(self, user_id: str,
                          dataset: str = None) -> list[dict]:
        """
        Get training history for a specific user.
        Used by simulation engine and Task A endpoint.
        """
        df = (self.load_train(dataset) if dataset
              else self.load_all_train())
        
        user_df = df[df["user_id"] == user_id].sort_values("date")
        return user_df.to_dict(orient="records")
    
    def get_test_items_for_user(self, user_id: str,
                                 dataset: str = None) -> list[dict]:
        """
        Get held-out test items for a specific user.
        Used by evaluation scripts.
        """
        df = (self.load_test(dataset) if dataset
              else self.load_all_test())
        
        user_df = df[df["user_id"] == user_id]
        return user_df.to_dict(orient="records")
    
    def get_available_datasets(self) -> list[str]:
        """Returns list of datasets that have been processed."""
        available = []
        for ds in self.DATASETS:
            if (self.PROCESSED_BASE / ds / "train.json").exists():
                available.append(ds)
        return available
    
    def dataset_stats(self) -> dict:
        """Print stats for all available datasets."""
        stats = {}
        for ds in self.DATASETS:
            train_path = self.PROCESSED_BASE / ds / "train.json"
            test_path  = self.PROCESSED_BASE / ds / "test.json"
            if train_path.exists():
                train = self._load(ds, "train")
                test  = self._load(ds, "test") if test_path.exists() \
                        else pd.DataFrame()
                stats[ds] = {
                    "train_records": len(train),
                    "test_records":  len(test),
                    "unique_users":  train["user_id"].nunique(),
                    "unique_items":  train["item_id"].nunique(),
                    "avg_rating":    round(train["rating"].mean(), 2),
                    "categories":    train["item_category"].value_counts()
                                         .head(5).to_dict(),
                }
        return stats
    
    def _load(self, dataset: str, split: str) -> pd.DataFrame:
        path = self.PROCESSED_BASE / dataset / f"{split}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Processed {dataset} {split} data not found at {path}. "
                f"Run the {dataset} pipeline first."
            )
        return pd.read_json(path, orient="records", lines=True)
```

---

## Nigerian Pattern Extractor — Runs Across All Three Datasets

```python
# data/datasets/nigerian_extractor.py

import pandas as pd
import json
from pathlib import Path

NIGERIAN_MARKERS = [
    # Pidgin
    "sha", "abi", "sef", "abeg", "na im", "e be like",
    "no be", "wetin", "oga", "wahala", "jare", "nau",
    # Nigerian English
    "very okay", "not too bad", "too much",
    # Nigerian food/culture
    "jollof", "suya", "pepper soup", "eba", "egusi",
    "puff puff", "akara", "banga",
    # Identity markers
    "naija", "9ja", "lagos", "abuja", "yoruba", "igbo",
    "hausa", "nigerian",
]

def detect_nigerian_markers(text: str) -> int:
    """Count Nigerian markers in text. Returns marker count."""
    text_lower = str(text).lower()
    return sum(1 for m in NIGERIAN_MARKERS if m in text_lower)

def extract_nigerian_users(df: pd.DataFrame,
                            min_markers: int = 2) -> pd.DataFrame:
    """
    Extract reviews exhibiting Nigerian language patterns.
    Works on any dataset in unified schema.
    """
    df = df.copy()
    df["nigerian_marker_count"] = df["review_text"].apply(
        detect_nigerian_markers
    )
    nigerian = df[df["nigerian_marker_count"] >= min_markers].copy()
    nigerian = nigerian.sort_values(
        "nigerian_marker_count", ascending=False
    )
    return nigerian

def extract_fewshot_examples(df: pd.DataFrame,
                              n: int = 20,
                              category: str = None) -> list[dict]:
    """
    Extract best few-shot examples for Nigerian prompt calibration.
    Optionally filter by category.
    """
    nigerian = extract_nigerian_users(df, min_markers=2)
    
    if category:
        filtered = nigerian[
            nigerian["item_category"].str.lower().str.contains(
                category.lower(), na=False
            )
        ]
        if len(filtered) >= 5:
            nigerian = filtered
    
    # Select examples with substantive review text (>50 chars)
    nigerian = nigerian[nigerian["review_text"].str.len() > 50]
    
    examples = nigerian.head(n)[
        ["item_name", "item_category", "rating", "review_text",
         "nigerian_marker_count"]
    ].to_dict(orient="records")
    
    return examples

def run_extraction_all_datasets():
    """Run Nigerian extraction across all processed datasets."""
    from unified_loader import UnifiedDatasetLoader
    
    loader = UnifiedDatasetLoader()
    available = loader.get_available_datasets()
    
    all_examples = []
    
    for dataset in available:
        print(f"\n[Nigerian Extractor] Processing {dataset}...")
        
        try:
            train = loader.load_train(dataset)
            nigerian = extract_nigerian_users(train, min_markers=2)
            
            # Save Nigerian users for this dataset
            output_path = (
                Path("data/processed") / dataset / "nigerian_users.json"
            )
            nigerian.to_json(output_path, orient="records", lines=True)
            
            print(f"  Nigerian-pattern reviews: {len(nigerian)}")
            print(f"  Saved to: {output_path}")
            
            # Extract few-shot examples
            examples = extract_fewshot_examples(nigerian, n=20)
            all_examples.extend(examples)
            
        except FileNotFoundError:
            print(f"  {dataset} not yet processed — skipping")
    
    # Save combined few-shot examples
    fewshot_path = Path("data/processed/nigerian_fewshots.json")
    with open(fewshot_path, "w") as f:
        json.dump(all_examples, f, indent=2)
    
    print(f"\n[Nigerian Extractor] Total few-shot examples: {len(all_examples)}")
    print(f"Saved to: {fewshot_path}")
    
    return all_examples

if __name__ == "__main__":
    run_extraction_all_datasets()
```

---

## Master Pipeline Runner — Runs Everything

```python
# data/datasets/run_all_pipelines.py
"""
Run this script to process all available datasets.
Skip any dataset whose raw files are not yet downloaded.

Usage:
    python data/datasets/run_all_pipelines.py

Download datasets first:
    Yelp:      https://www.yelp.com/dataset
    Amazon:    https://amazon-reviews-2023.github.io
    Goodreads: https://mengtingwan.github.io/data/goodreads
"""

from pathlib import Path

def run():
    results = {}
    
    # --- Yelp ---
    yelp_check = Path("data/raw/yelp/yelp_academic_dataset_review.json")
    if yelp_check.exists():
        print("\n" + "="*50)
        print("PROCESSING YELP")
        print("="*50)
        from yelp_pipeline import YelpPipeline
        pipeline = YelpPipeline()
        train, test = pipeline.run()
        results["yelp"] = {
            "train": len(train), "test": len(test)
        }
    else:
        print(f"\n[SKIP] Yelp raw data not found at {yelp_check}")
        print("  Download from: https://www.yelp.com/dataset")
    
    # --- Amazon ---
    amazon_files = list(Path("data/raw/amazon").glob("*.jsonl*"))
    if amazon_files:
        print("\n" + "="*50)
        print("PROCESSING AMAZON")
        print("="*50)
        from amazon_pipeline import AmazonPipeline
        pipeline = AmazonPipeline()
        train, test = pipeline.run()
        results["amazon"] = {
            "train": len(train), "test": len(test)
        }
    else:
        print("\n[SKIP] Amazon raw data not found in data/raw/amazon/")
        print("  Download from: https://amazon-reviews-2023.github.io")
    
    # --- Goodreads ---
    gr_files = list(Path("data/raw/goodreads").glob("*.json.gz"))
    if gr_files:
        print("\n" + "="*50)
        print("PROCESSING GOODREADS")
        print("="*50)
        from goodreads_pipeline import GoodreadsPipeline
        pipeline = GoodreadsPipeline()
        train, test = pipeline.run()
        results["goodreads"] = {
            "train": len(train), "test": len(test)
        }
    else:
        print("\n[SKIP] Goodreads raw data not found in data/raw/goodreads/")
        print("  Download from: https://mengtingwan.github.io/data/goodreads")
    
    # --- Nigerian Extraction (runs on whatever was processed) ---
    if results:
        print("\n" + "="*50)
        print("EXTRACTING NIGERIAN PATTERNS")
        print("="*50)
        from nigerian_extractor import run_extraction_all_datasets
        run_extraction_all_datasets()
    
    # --- Summary ---
    print("\n" + "="*50)
    print("PIPELINE COMPLETE — SUMMARY")
    print("="*50)
    
    if not results:
        print("No datasets were processed.")
        print("Download at least one dataset and re-run.")
    else:
        for dataset, counts in results.items():
            print(f"  {dataset.capitalize()}:")
            print(f"    Train: {counts['train']:,} records")
            print(f"    Test:  {counts['test']:,} records")
        
        print("\nNext step: Run evaluation scripts")
        print("  python data/evaluation/run_evaluation.py")

if __name__ == "__main__":
    run()
```

---

## What To Add To requirements.txt

```
# Add these if not already present
rouge-score>=0.1.2
pandas>=2.0.0
numpy>=1.24.0
```

---

## What To Do Right Now

**Step 1 — Build the files**
Create all files in this document exactly as specified.
Do not modify any existing files except to add
`from data.datasets.unified_loader import UnifiedDatasetLoader`
where dataset access is needed.

**Step 2 — Create the directory structure**
```
data/
  raw/
    yelp/         ← empty, user downloads here
    amazon/       ← empty, user downloads here
    goodreads/    ← empty, user downloads here
  processed/
    yelp/         ← pipeline writes here
    amazon/       ← pipeline writes here
    goodreads/    ← pipeline writes here
  datasets/
    __init__.py
    yelp_pipeline.py
    amazon_pipeline.py
    goodreads_pipeline.py
    unified_loader.py
    nigerian_extractor.py
    run_all_pipelines.py
```

**Step 3 — Verify existing tests still pass**
After creating all new files, run:
```
python -m pytest test_integration.py test_performance.py -v
```
All 20 tests must still pass.

**Step 4 — Add README section**
Add a "Dataset Setup" section to README.md:
```markdown
## Dataset Setup

Download at least one dataset before running evaluation:

| Dataset | Download | Place in |
|---|---|---|
| Yelp | https://www.yelp.com/dataset | data/raw/yelp/ |
| Amazon | https://amazon-reviews-2023.github.io | data/raw/amazon/ |
| Goodreads | https://mengtingwan.github.io/data/goodreads | data/raw/goodreads/ |

Then run:
    python data/datasets/run_all_pipelines.py
```

**Step 5 — Move to evaluation scripts**
Once all pipeline files are created and tests pass,
proceed to build `data/evaluation/task_a_evaluator.py`
and `data/evaluation/task_b_evaluator.py` per the
original alignment prompt.

---

## Rules — Do Not Break These

```
1. All 20 existing tests must still pass after this work.
2. mock_data/ is not touched or removed.
3. Pipeline files go in data/datasets/ — not in root.
4. All three pipelines output IDENTICAL schema.
5. UnifiedDatasetLoader is the ONLY interface agents use.
6. Pipelines gracefully skip if raw files not yet downloaded.
7. No pipeline modifies main.py, pipeline.py, or memory_manager.py.
```

---

*ARCHE Dataset Pipeline Instruction v1.0 — May 2026*
*Give this file alongside ARCHE_Copilot_Alignment_Prompt.md*
*and ARCHE_HackAlign.md*
