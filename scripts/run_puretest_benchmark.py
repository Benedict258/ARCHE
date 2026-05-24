from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from api.main import app
from agents.recommendation_scoring import build_simulation_from_history, rank_catalog_against_simulation
from data.evaluation.task_a_evaluator import TaskAEvaluator
from data.evaluation.task_b_evaluator import TaskBEvaluator

ROOT = Path(__file__).resolve().parents[1]
PURETEST = ROOT / "data" / "puretest"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_catalog() -> list[dict[str, Any]]:
    return read_jsonl(PURETEST / "catalog.jsonl")


def run_task_a(client: TestClient, cases: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    evaluator = TaskAEvaluator()
    results: list[dict[str, Any]] = []
    for case in cases:
        payload = {
            "user_token": case["user_token"],
            "user_history": case["user_history"],
            "item": case["item"],
            "context": case.get("context", {}),
        }
        response = client.post("/v1/simulate-review", json=payload)
        response.raise_for_status()
        body = response.json()
        results.append(
            {
                "user_token": case["user_token"],
                "predicted_rating": body["predicted_rating"],
                "actual_rating": case["actual_rating"],
                "generated_review": body["generated_review"],
                "actual_review": case["actual_review"],
                "user_history_text": [entry.get("review_text", "") for entry in case["user_history"]],
            }
        )
    return evaluator.evaluate(results), results


def run_task_b(cases: list[dict[str, Any]], catalog: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    evaluator = TaskBEvaluator()
    results: list[dict[str, Any]] = []
    for case in cases:
        history = case.get("user_persona", {}).get("review_history", [])
        context = case.get("context", {})
        sim = build_simulation_from_history(history, context)
        ranked = rank_catalog_against_simulation(sim, catalog, n=10)
        recommended = [item.get("item_id") or item.get("key") for item in ranked]
        results.append(
            {
                "user_token": case["user_token"],
                "recommended_items": recommended,
                "relevant_items": case.get("relevant_items") or case.get("ground_truth") or [],
                "is_cold_start": bool(sim.get("cold_start_used")),
                "user_domain": case.get("source"),
            }
        )
    return evaluator.evaluate(results, k=10), results


def main() -> int:
    task_a_cases = read_jsonl(PURETEST / "task_a_cases.jsonl")
    task_b_cases = read_jsonl(PURETEST / "task_b_cases.jsonl")
    catalog = load_catalog()

    client = TestClient(app)

    task_a_metrics, task_a_results = run_task_a(client, task_a_cases)
    task_b_metrics, task_b_results = run_task_b(task_b_cases, catalog)

    report = {
        "task_a": {
            "metrics": task_a_metrics,
            "n_cases": len(task_a_results),
        },
        "task_b": {
            "metrics": task_b_metrics,
            "n_cases": len(task_b_results),
        },
        "puretest_manifest": json.loads((PURETEST / "manifest.json").read_text(encoding="utf-8")),
    }

    (PURETEST / "puretest_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
