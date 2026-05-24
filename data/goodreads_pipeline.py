from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _import_pandas():
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - import guard
        raise ImportError(
            "pandas is required for the Goodreads pipeline. Install it with `pip install pandas`."
        ) from exc
    return pd


class GoodreadsPipeline:
    """Process Goodreads review data for ARCHE evaluation.

    Expected raw files inside `raw_dir`:
    - books.jsonl or books.csv (optional metadata)
    - reviews.jsonl or reviews.csv
    """

    def __init__(self, raw_dir: str = "data/goodreads_raw", processed_dir: str = "data/goodreads_processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _load_json_lines(self, file_name: str, max_records: int | None = None):
        pd = _import_pandas()
        path = self.raw_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"Missing Goodreads source file: {path}.")

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

    def _load_csv(self, file_name: str):
        pd = _import_pandas()
        path = self.raw_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"Missing Goodreads source file: {path}.")
        return pd.read_csv(path)

    def load_reviews(self, max_records: int = 500_000):
        jsonl = self.raw_dir / "reviews.jsonl"
        csv = self.raw_dir / "reviews.csv"
        if jsonl.exists():
            return self._load_json_lines("reviews.jsonl", max_records=max_records)
        if csv.exists():
            return self._load_csv("reviews.csv")
        raise FileNotFoundError("No Goodreads reviews file found. Expected reviews.jsonl or reviews.csv.")

    def load_books(self, required_book_ids: set[str] | None = None):
        jsonl = self.raw_dir / "books.jsonl"
        csv = self.raw_dir / "books.csv"
        if jsonl.exists():
            if not required_book_ids:
                return self._load_json_lines("books.jsonl")

            pd = _import_pandas()
            records: list[dict[str, Any]] = []
            with jsonl.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if str(record.get("book_id") or "") in required_book_ids:
                        records.append(record)
                        if len(records) >= len(required_book_ids):
                            break
            return pd.DataFrame(records)
        if csv.exists():
            books = self._load_csv("books.csv")
            if required_book_ids and "book_id" in books.columns:
                return books[books["book_id"].astype(str).isin(required_book_ids)].copy()
            return books
        return None

    def build_user_profiles(self, min_reviews: int = 10):
        pd = _import_pandas()
        reviews = self.load_reviews()

        if reviews.empty:
            return reviews

        user_col = "user_id" if "user_id" in reviews.columns else ("user_id" if "user_id" in reviews.columns else None)
        if user_col is None:
            possible_cols = [c for c in reviews.columns if c.lower() in {"user_id", "user", "author_id", "reviewerid"}]
            if not possible_cols:
                raise ValueError("Goodreads reviews must contain a user identifier column.")
            user_col = possible_cols[0]

        counts = reviews.groupby(user_col).size()
        active_users = counts[counts >= min_reviews].index
        reviews = reviews[reviews[user_col].isin(active_users)].copy()

        if "rating" not in reviews.columns:
            for candidate in ["user_rating", "stars", "score"]:
                if candidate in reviews.columns:
                    reviews = reviews.rename(columns={candidate: "rating"})
                    break

        reviews = reviews.rename(columns={user_col: "user_id"})
        date_col = next((col for col in ["date", "date_added", "read_at", "date_updated"] if col in reviews.columns), None)
        if date_col:
            reviews["date"] = pd.to_datetime(reviews[date_col], errors="coerce", utc=True)

        required_book_ids = set()
        if "book_id" in reviews.columns:
            required_book_ids = {str(book_id) for book_id in reviews["book_id"].dropna().astype(str).unique()}

        books = self.load_books(required_book_ids=required_book_ids)
        if books is not None and not books.empty:
            book_key = None
            for candidate in ["book_id", "bookID", "isbn", "title"]:
                if candidate in books.columns and candidate in reviews.columns:
                    book_key = candidate
                    break
            if book_key:
                merge_cols = [col for col in [book_key, "title", "authors", "categories"] if col in books.columns]
                reviews = reviews.merge(books[merge_cols], on=book_key, how="left")

        return reviews

    def train_test_split(self, reviews_df, test_ratio: float = 0.2):
        pd = _import_pandas()
        if reviews_df.empty:
            raise ValueError("reviews_df is empty; cannot split Goodreads data.")

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

        text_col = next((c for c in ["review_text", "text", "reviewText", "comment"] if c in reviews_df.columns), None)
        if reviews_df.empty or text_col is None:
            nigerian = reviews_df.iloc[0:0].copy()
        else:
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
    pipeline = GoodreadsPipeline()
    pipeline.run()
