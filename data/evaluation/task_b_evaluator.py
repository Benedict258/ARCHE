from __future__ import annotations

import math
from typing import Any, Iterable


class TaskBEvaluator:
    """Evaluate Task B (recommendation) outputs.

    Provides:
    - NDCG@k
    - Hit Rate@k
    - simple aggregate evaluation helper
    """

    @staticmethod
    def _normalize_relevant(relevant: Iterable[Any]) -> set[Any]:
        return set(relevant or [])

    def ndcg_at_k(self, recommended: list[Any], relevant: Iterable[Any], k: int = 10) -> float:
        relevant_set = self._normalize_relevant(relevant)
        if not relevant_set or not recommended:
            return 0.0

        dcg = 0.0
        for idx, item in enumerate(recommended[:k]):
            if item in relevant_set:
                dcg += 1.0 / math.log2(idx + 2)

        ideal_hits = min(len(relevant_set), k)
        idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
        return dcg / idcg if idcg > 0 else 0.0

    def hit_rate_at_k(self, recommended: list[Any], relevant: Iterable[Any], k: int = 10) -> float:
        relevant_set = self._normalize_relevant(relevant)
        if not relevant_set or not recommended:
            return 0.0
        return float(bool(set(recommended[:k]) & relevant_set))

    def precision_at_k(self, recommended: list[Any], relevant: Iterable[Any], k: int = 10) -> float:
        relevant_set = self._normalize_relevant(relevant)
        if not relevant_set or not recommended:
            return 0.0
        top_k = recommended[:k]
        return len([item for item in top_k if item in relevant_set]) / min(k, len(top_k))

    def evaluate(self, results: list[dict[str, Any]], k: int = 10) -> dict[str, Any]:
        """Evaluate recommendation results.

        Expected result keys:
        - recommended_items / recommendations
        - relevant_items / ground_truth
        """
        if not results:
            return {"ndcg_at_k": 0.0, "hit_rate_at_k": 0.0, "precision_at_k": 0.0, "n_samples": 0, "k": k}

        ndcg_scores = []
        hit_scores = []
        precision_scores = []

        for result in results:
            recommended = result.get("recommended_items") or result.get("recommendations") or []
            relevant = result.get("relevant_items") or result.get("ground_truth") or result.get("relevant") or []

            ndcg_scores.append(self.ndcg_at_k(recommended, relevant, k=k))
            hit_scores.append(self.hit_rate_at_k(recommended, relevant, k=k))
            precision_scores.append(self.precision_at_k(recommended, relevant, k=k))

        return {
            "ndcg_at_k": sum(ndcg_scores) / len(ndcg_scores),
            "hit_rate_at_k": sum(hit_scores) / len(hit_scores),
            "precision_at_k": sum(precision_scores) / len(precision_scores),
            "n_samples": len(results),
            "k": k,
        }
