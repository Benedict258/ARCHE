from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .task_a_evaluator import TaskAEvaluator
from .task_b_evaluator import TaskBEvaluator


class EvaluationRunner:
    """Convenience runner for Task A / Task B evaluation artifacts."""

    def __init__(self):
        self.task_a = TaskAEvaluator()
        self.task_b = TaskBEvaluator()

    @staticmethod
    def _load_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def run_task_a(self, results_path: Path) -> dict[str, Any]:
        payload = self._load_json(results_path)
        results = payload if isinstance(payload, list) else payload.get("results", [])
        metrics = self.task_a.evaluate(results)
        return {"task": "A", "source": str(results_path), "metrics": metrics}

    def run_task_b(self, results_path: Path, k: int = 10) -> dict[str, Any]:
        payload = self._load_json(results_path)
        results = payload if isinstance(payload, list) else payload.get("results", [])
        metrics = self.task_b.evaluate(results, k=k)
        return {"task": "B", "source": str(results_path), "metrics": metrics}

    def run(self, task: str, results_path: Path, k: int = 10) -> dict[str, Any]:
        if task.upper() == "A":
            return self.run_task_a(results_path)
        if task.upper() == "B":
            return self.run_task_b(results_path, k=k)
        raise ValueError("task must be 'A' or 'B'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ARCHE evaluation metrics for Task A or Task B.")
    parser.add_argument("task", choices=["A", "B"], help="Task to evaluate")
    parser.add_argument("results_path", help="Path to a JSON file containing evaluation results")
    parser.add_argument("--k", type=int, default=10, help="Cutoff for Task B ranking metrics")
    args = parser.parse_args()

    runner = EvaluationRunner()
    report = runner.run(args.task, Path(args.results_path), k=args.k)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())