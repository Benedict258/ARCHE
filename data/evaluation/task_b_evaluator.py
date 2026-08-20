"""Task B (recommendation) offline evaluation: precision/recall/hit-rate/NDCG@k."""

from __future__ import annotations

import math
from statistics import mean
from typing import Any


def _dcg_at_k(ranked_relevance: list[int], k: int) -> float:
    return sum(rel / math.log2(idx + 2) for idx, rel in enumerate(ranked_relevance[:k]))


def _ndcg_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    ranked_relevance = [1 if item in relevant else 0 for item in recommended[:k]]
    dcg = _dcg_at_k(ranked_relevance, k)
    ideal_relevance = [1] * min(len(relevant), k)
    idcg = _dcg_at_k(ideal_relevance, k)
    return dcg / idcg if idcg > 0 else 0.0


class TaskBEvaluator:
    """Scores a batch of Task B recommendation runs against ground-truth relevant items."""

    def evaluate(self, results: list[dict[str, Any]], k: int = 10) -> dict[str, Any]:
        if not results:
            return {"n": 0}

        precisions: list[float] = []
        recalls: list[float] = []
        hits: list[bool] = []
        ndcgs: list[float] = []
        cold_start_count = 0

        for result in results:
            recommended = [str(item) for item in (result.get("recommended_items") or []) if item]
            relevant = {str(item) for item in (result.get("relevant_items") or []) if item}
            if result.get("is_cold_start"):
                cold_start_count += 1

            top_k = recommended[:k]
            hit_count = len(set(top_k) & relevant)

            precisions.append(hit_count / k if k else 0.0)
            recalls.append(hit_count / len(relevant) if relevant else 0.0)
            hits.append(hit_count > 0)
            ndcgs.append(_ndcg_at_k(recommended, relevant, k))

        return {
            "n": len(results),
            "k": k,
            f"precision_at_{k}": round(mean(precisions), 4),
            f"recall_at_{k}": round(mean(recalls), 4),
            f"hit_rate_at_{k}": round(mean(hits), 4),
            f"ndcg_at_{k}": round(mean(ndcgs), 4),
            "cold_start_ratio": round(cold_start_count / len(results), 4),
        }
