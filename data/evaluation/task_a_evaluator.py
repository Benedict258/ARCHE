from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any


class TaskAEvaluator:
    """Evaluate Task A (simulate-review) outputs.

    Provides:
    - RMSE for star-rating prediction
    - ROUGE-1/2/L style overlap scores implemented in pure Python
    """

    _token_re = re.compile(r"\w+", re.UNICODE)

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        return cls._token_re.findall((text or "").lower())

    @staticmethod
    def rmse(predicted: list[int | float], actual: list[int | float]) -> float:
        if len(predicted) != len(actual):
            raise ValueError("predicted and actual must have the same length")
        if not predicted:
            return 0.0
        return math.sqrt(sum((float(p) - float(a)) ** 2 for p, a in zip(predicted, actual)) / len(predicted))

    @staticmethod
    def _ngram_counts(tokens: list[str], n: int) -> Counter[tuple[str, ...]]:
        if n <= 0 or len(tokens) < n:
            return Counter()
        return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))

    @staticmethod
    def _precision_recall_f1(overlap: int, predicted_total: int, reference_total: int) -> dict[str, float]:
        precision = overlap / predicted_total if predicted_total else 0.0
        recall = overlap / reference_total if reference_total else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        return {"precision": precision, "recall": recall, "f1": f1}

    @classmethod
    def rouge_n(cls, reference: str, generated: str, n: int) -> dict[str, float]:
        ref_tokens = cls.tokenize(reference)
        gen_tokens = cls.tokenize(generated)
        ref_counts = cls._ngram_counts(ref_tokens, n)
        gen_counts = cls._ngram_counts(gen_tokens, n)

        overlap = sum((ref_counts & gen_counts).values())
        return cls._precision_recall_f1(overlap, sum(gen_counts.values()), sum(ref_counts.values()))

    @staticmethod
    def _lcs_length(a: list[str], b: list[str]) -> int:
        if not a or not b:
            return 0
        prev = [0] * (len(b) + 1)
        for token_a in a:
            curr = [0]
            for j, token_b in enumerate(b, start=1):
                if token_a == token_b:
                    curr.append(prev[j - 1] + 1)
                else:
                    curr.append(max(prev[j], curr[-1]))
            prev = curr
        return prev[-1]

    @classmethod
    def rouge_l(cls, reference: str, generated: str) -> dict[str, float]:
        ref_tokens = cls.tokenize(reference)
        gen_tokens = cls.tokenize(generated)
        lcs = cls._lcs_length(ref_tokens, gen_tokens)
        return cls._precision_recall_f1(lcs, len(gen_tokens), len(ref_tokens))

    def rouge_scores(self, generated: list[str], reference: list[str]) -> dict[str, float]:
        if len(generated) != len(reference):
            raise ValueError("generated and reference must have the same length")
        if not generated:
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

        rouge1_scores = []
        rouge2_scores = []
        rouge_l_scores = []
        for ref, gen in zip(reference, generated):
            rouge1_scores.append(self.rouge_n(ref, gen, 1)["f1"])
            rouge2_scores.append(self.rouge_n(ref, gen, 2)["f1"])
            rouge_l_scores.append(self.rouge_l(ref, gen)["f1"])

        return {
            "rouge1": sum(rouge1_scores) / len(rouge1_scores),
            "rouge2": sum(rouge2_scores) / len(rouge2_scores),
            "rougeL": sum(rouge_l_scores) / len(rouge_l_scores),
        }

    def evaluate(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Evaluate a list of Task A result dictionaries.

        Expected keys per result:
        - predicted_rating
        - actual_rating
        - generated_review
        - actual_review
        """
        if not results:
            return {"rmse": 0.0, "rouge": {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}, "n_samples": 0}

        predicted_ratings = [r["predicted_rating"] for r in results]
        actual_ratings = [r["actual_rating"] for r in results]
        generated_reviews = [r["generated_review"] for r in results]
        actual_reviews = [r["actual_review"] for r in results]

        return {
            "rmse": self.rmse(predicted_ratings, actual_ratings),
            "rouge": self.rouge_scores(generated_reviews, actual_reviews),
            "n_samples": len(results),
        }
