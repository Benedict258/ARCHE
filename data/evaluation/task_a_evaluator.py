"""Task A (review generation) offline evaluation.

Deliberately dependency-light: rating error is exact math, and the text
metrics use stdlib `difflib` rather than a BERTScore/transformer model. That's
a real but rougher signal — swapping in a proper semantic-similarity metric
later (e.g. via the Voyage embeddings already wired up for Task B) is a cheap
upgrade once this baseline proves useful.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from statistics import mean
from typing import Any


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _ngrams(tokens: list[str], n: int = 8) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def _leaks_history(generated_review: str, history_texts: list[str], n: int = 8) -> bool:
    """True if the generated review shares a long verbatim run with any history text."""
    generated_ngrams = _ngrams(_tokenize(generated_review), n)
    if not generated_ngrams:
        return False
    for history_text in history_texts:
        if generated_ngrams & _ngrams(_tokenize(history_text), n):
            return True
    return False


class TaskAEvaluator:
    """Scores a batch of Task A predictions against ground truth."""

    def evaluate(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        if not results:
            return {"n": 0}

        rating_errors: list[float] = []
        within_one: list[bool] = []
        text_similarities: list[float] = []
        leaked_flags: list[bool] = []

        for result in results:
            predicted = float(result.get("predicted_rating") or 0.0)
            actual = float(result.get("actual_rating") or 0.0)
            error = predicted - actual
            rating_errors.append(error)
            within_one.append(abs(error) <= 1.0)

            generated_review = str(result.get("generated_review") or "")
            actual_review = str(result.get("actual_review") or "")
            if actual_review:
                text_similarities.append(SequenceMatcher(None, generated_review.lower(), actual_review.lower()).ratio())

            history_texts = [str(t) for t in (result.get("user_history_text") or []) if t]
            leaked_flags.append(_leaks_history(generated_review, history_texts))

        mae = mean(abs(e) for e in rating_errors)
        rmse = mean(e * e for e in rating_errors) ** 0.5

        return {
            "n": len(results),
            "rating_mae": round(mae, 4),
            "rating_rmse": round(rmse, 4),
            "rating_within_1_star": round(mean(within_one), 4),
            "text_similarity_to_actual": round(mean(text_similarities), 4) if text_similarities else None,
            "history_leakage_rate": round(mean(leaked_flags), 4),
        }
