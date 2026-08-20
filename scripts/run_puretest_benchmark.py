from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from api.main import app
from agents.simulation_agent import SimulationAgent
from agents.recommendation_pipeline import run_recommendation_pipeline
from data.evaluation.task_a_evaluator import TaskAEvaluator
from data.evaluation.task_b_evaluator import TaskBEvaluator

ROOT = Path(__file__).resolve().parents[1]
PURETEST = ROOT / "data" / "puretest"

# Force every SimulationAgent onto its heuristic fallback path so benchmark
# runs are deterministic and reproducible regardless of what LLM keys happen
# to be configured in the environment — the same discipline tests/conftest.py
# already applies to the pytest suite.
SimulationAgent._init_llm = lambda self: (setattr(self, "llm", None), setattr(self, "llm_provider", None))


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


async def _recommend_for_case(case: dict[str, Any], catalog: list[dict[str, Any]]) -> dict[str, Any]:
    history = case.get("user_persona", {}).get("review_history", [])
    context = case.get("context", {})
    out = await run_recommendation_pipeline(
        user_token=case["user_token"],
        lookup_token=case["user_token"],
        user_history=history,
        context=context,
        domain_filter="",
        n=10,
        item_pool=catalog,
        enable_live_data=False,
        live_query=None,
        live_results_limit=5,
        memory_manager=None,
    )
    recommended = [rec.get("item_id") for rec in out["recommendations"]]
    return {
        "user_token": case["user_token"],
        "recommended_items": recommended,
        "relevant_items": case.get("relevant_items") or case.get("ground_truth") or [],
        "is_cold_start": bool(out.get("cold_start_handled")),
        "user_domain": case.get("source"),
    }


async def _run_task_b_async(cases: list[dict[str, Any]], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [await _recommend_for_case(case, catalog) for case in cases]


def run_task_b(cases: list[dict[str, Any]], catalog: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Runs each case through the real recommendation pipeline (agents/recommendation_pipeline.py) —
    the same code /v1/recommend serves — against the fixed puretest catalog so
    `relevant_items` (drawn from that catalog) are meaningfully comparable."""
    evaluator = TaskBEvaluator()
    results = asyncio.run(_run_task_b_async(cases, catalog))
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
