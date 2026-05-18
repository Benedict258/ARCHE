from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _import_pandas():
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - defensive import guard
        raise ImportError(
            "pandas is required for the Yelp pipeline. Install it with `pip install pandas`."
        ) from exc
    return pd


class YelpPipeline:
    """Process the Yelp Open Dataset for ARCHE evaluation.

    Expected raw files inside `raw_dir`:
    - yelp_academic_dataset_review.json
    - yelp_academic_dataset_business.json
    """

    def __init__(self, raw_dir: str = "data/yelp_raw", processed_dir: str = "data/yelp_processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _load_json_lines(self, file_name: str, max_records: int | None = None):
        pd = _import_pandas()
        path = self.raw_dir / file_name
        if not path.exists():
            raise FileNotFoundError(
                f"Missing Yelp source file: {path}. Download the Yelp Open Dataset and place the JSON file there."
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
        """Load review records from the Yelp reviews JSONL file."""
        return self._load_json_lines("yelp_academic_dataset_review.json", max_records=max_records)

    def load_businesses(self):
        """Load business metadata from the Yelp businesses JSONL file."""
        return self._load_json_lines("yelp_academic_dataset_business.json")

    def build_user_profiles(self, min_reviews: int = 10):
        """Build filtered user review profiles with business metadata joined in."""
        pd = _import_pandas()

        reviews = self.load_reviews()
        businesses = self.load_businesses()

        if reviews.empty:
            return reviews

        counts = reviews.groupby("user_id").size()
        active_users = counts[counts >= min_reviews].index
        reviews = reviews[reviews["user_id"].isin(active_users)].copy()

        business_cols = [col for col in ["business_id", "name", "categories", "city", "state", "stars"] if col in businesses.columns]
        if business_cols:
            reviews = reviews.merge(businesses[business_cols], on="business_id", how="left")

        if "date" in reviews.columns:
            reviews["date"] = pd.to_datetime(reviews["date"], errors="coerce")

        return reviews

    def train_test_split(self, reviews_df, test_ratio: float = 0.2):
        """Split each user's history chronologically: last test_ratio is held out."""
        pd = _import_pandas()

        if reviews_df.empty:
            raise ValueError("reviews_df is empty; cannot split data.")
        if "user_id" not in reviews_df.columns:
            raise ValueError("reviews_df must contain a user_id column.")

        if "date" in reviews_df.columns:
            reviews_sorted = reviews_df.sort_values(["user_id", "date"])
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
        """Extract reviews that show Nigerian language markers for calibration."""
        pd = _import_pandas()

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

        if reviews_df.empty or "text" not in reviews_df.columns:
            nigerian = reviews_df.iloc[0:0].copy()
        else:
            text_series = reviews_df["text"].fillna("").astype(str).str.lower()
            mask = text_series.apply(lambda t: sum(marker in t for marker in markers) >= min_markers)
            nigerian = reviews_df[mask].copy()

        nigerian.to_json(self.processed_dir / "nigerian_users.json", orient="records", lines=True, force_ascii=False)
        return nigerian

    def run(self, min_reviews: int = 10, test_ratio: float = 0.2):
        """Run the full preprocessing flow and return train/test splits."""
        reviews = self.build_user_profiles(min_reviews=min_reviews)
        train, test = self.train_test_split(reviews, test_ratio=test_ratio)
        self.extract_nigerian_users(reviews)
        return train, test


if __name__ == "__main__":
    pipeline = YelpPipeline()
    pipeline.run()