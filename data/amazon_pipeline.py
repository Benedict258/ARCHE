from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _import_pandas():
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - import guard
        raise ImportError(
            "pandas is required for the Amazon pipeline. Install it with `pip install pandas`."
        ) from exc
    return pd


class AmazonPipeline:
    """Process Amazon review data for ARCHE evaluation.

    Expected raw files inside `raw_dir`:
    - reviews.jsonl (or a custom review JSONL file)
    - products.jsonl (optional)
    """

    def __init__(self, raw_dir: str = "data/amazon_raw", processed_dir: str = "data/amazon_processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _load_json_lines(self, file_name: str, max_records: int | None = None):
        pd = _import_pandas()
        path = self.raw_dir / file_name
        if not path.exists():
            raise FileNotFoundError(
                f"Missing Amazon source file: {path}. Place the JSONL review export there."
            )

        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for idx, line in enumerate(handle):
                if max_records is not None and idx >= max_records:
                    break
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return pd.DataFrame(records)

    def load_reviews(self, max_records: int = 500_000):
        return self._load_json_lines("reviews.jsonl", max_records=max_records)

    def load_products(self):
        products_path = self.raw_dir / "products.jsonl"
        if not products_path.exists():
            return None
        return self._load_json_lines("products.jsonl")

    def build_user_profiles(self, min_reviews: int = 10):
        pd = _import_pandas()
        reviews = self.load_reviews()

        if reviews.empty:
            return reviews

        user_col = "reviewerID" if "reviewerID" in reviews.columns else "user_id"
        time_col = "unixReviewTime" if "unixReviewTime" in reviews.columns else "date"

        counts = reviews.groupby(user_col).size()
        active_users = counts[counts >= min_reviews].index
        reviews = reviews[reviews[user_col].isin(active_users)].copy()

        if time_col in reviews.columns:
            reviews[time_col] = pd.to_datetime(reviews[time_col], errors="coerce", unit="s" if time_col == "unixReviewTime" else None)

        reviews = reviews.rename(columns={user_col: "user_id"})
        return reviews

    def train_test_split(self, reviews_df, test_ratio: float = 0.2):
        pd = _import_pandas()
        if reviews_df.empty:
            raise ValueError("reviews_df is empty; cannot split Amazon data.")

        sort_col = "unixReviewTime" if "unixReviewTime" in reviews_df.columns else ("date" if "date" in reviews_df.columns else None)
        if sort_col:
            reviews_sorted = reviews_df.sort_values(["user_id", sort_col])
        else:
            reviews_sorted = reviews_df.sort_values(["user_id"])

        train_parts = []
        test_parts = []
        for _, group in reviews_sorted.groupby("user_id"):
            if len(group) < 2:
                train_parts.append(group)
                continue
            split_idx = max(1, int(len(group) * (1 - test_ratio)))
            split_idx = min(split_idx, len(group) - 1)
            train_parts.append(group.iloc[:split_idx])
            test_parts.append(group.iloc[split_idx:])

        train = pd.concat(train_parts, ignore_index=True) if train_parts else reviews_sorted.iloc[0:0].copy()
        test = pd.concat(test_parts, ignore_index=True) if test_parts else reviews_sorted.iloc[0:0].copy()

        train.to_json(self.processed_dir / "train.json", orient="records", lines=True, force_ascii=False)
        test.to_json(self.processed_dir / "test.json", orient="records", lines=True, force_ascii=False)
        return train, test

    def extract_nigerian_users(self, reviews_df, min_markers: int = 2):
        markers = [
            "sha",
            "abi",
            "sef",
            "abeg",
            "na im",
            "e be like",
            "very okay",
            "jollof",
            "suya",
            "pepper soup",
            "naija",
            "9ja",
        ]

        if reviews_df.empty or "reviewText" not in reviews_df.columns and "text" not in reviews_df.columns:
            nigerian = reviews_df.iloc[0:0].copy()
        else:
            text_col = "reviewText" if "reviewText" in reviews_df.columns else "text"
            text_series = reviews_df[text_col].fillna("").astype(str).str.lower()
            mask = text_series.apply(lambda t: sum(marker in t for marker in markers) >= min_markers)
            nigerian = reviews_df[mask].copy()

        nigerian.to_json(self.processed_dir / "nigerian_users.json", orient="records", lines=True, force_ascii=False)
        return nigerian

    def run(self, min_reviews: int = 10, test_ratio: float = 0.2):
        reviews = self.build_user_profiles(min_reviews=min_reviews)
        train, test = self.train_test_split(reviews, test_ratio=test_ratio)
        self.extract_nigerian_users(reviews)
        return train, test


if __name__ == "__main__":
    pipeline = AmazonPipeline()
    pipeline.run()