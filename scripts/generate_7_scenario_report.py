from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE_URL = "http://localhost:8000"
ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
REPORT_PATH = REPORT_DIR / "comprehensive_test_report_7_scenarios.md"
JSON_PATH = REPORT_DIR / "comprehensive_test_report_7_scenarios.json"


def _post(path: str, payload: dict[str, Any], timeout: int = 60) -> tuple[int, Any]:
    response = requests.post(f"{BASE_URL}{path}", json=payload, timeout=timeout)
    try:
        body = response.json()
    except Exception:
        body = response.text
    return response.status_code, body


def run() -> int:
    scenarios: list[dict[str, Any]] = []

    # Scenario 1: Task A formal profile, schema alias path
    s1_payload = {
        "user_persona": {
            "user_id": "s1_formal",
            "review_history": [
                {
                    "item_name": "Atomic Habits",
                    "category": "books",
                    "rating": 4,
                    "review_text": "A practical and well-researched guide to behaviour change.",
                },
                {
                    "item_name": "Sony WH-1000XM5",
                    "category": "electronics",
                    "rating": 5,
                    "review_text": "Outstanding quality and great noise cancellation.",
                },
            ],
        },
        "item_details": {
            "name": "Half of a Yellow Sun",
            "category": "african_literature",
            "price_tier": "mid",
            "attributes": {"author": "Chimamanda Ngozi Adichie"},
        },
        "context": {"time_of_day": "afternoon", "region": "Lagos Island"},
    }
    s1_status, s1_body = _post("/v1/simulate-review", s1_payload)
    scenarios.append(
        {
            "id": "S1",
            "name": "Task A Formal Persona",
            "endpoint": "/v1/simulate-review",
            "status": s1_status,
            "checks": {
                "has_llm_instrumentation": isinstance(s1_body, dict) and "llm_instrumentation" in s1_body,
                "has_behavioural_basis": isinstance(s1_body, dict) and bool(s1_body.get("behavioural_basis")),
                "no_atomic_copy_leak": isinstance(s1_body, dict)
                and "a practical and well-researched guide" not in str(s1_body.get("generated_review", "")).lower(),
            },
            "response": s1_body,
        }
    )

    # Scenario 2: Task A mixed pidgin profile
    s2_payload = {
        "user_persona": {
            "user_id": "s2_pidgin",
            "review_history": [
                {
                    "item_name": "Mr Biggs",
                    "item_category": "fast_food",
                    "rating": 2,
                    "review_text": "Abeg make dem upgrade this place.",
                },
                {
                    "item_name": "Chicken Republic",
                    "item_category": "fast_food",
                    "rating": 4,
                    "review_text": "Always consistent and good value.",
                },
            ],
        },
        "item_details": {
            "name": "The Place Restaurant Lekki",
            "category": "food",
            "price_tier": "mid",
            "attributes": {"cuisine": "Nigerian"},
        },
        "context": {"time_of_day": "evening", "region": "Lagos Mainland"},
    }
    s2_status, s2_body = _post("/v1/simulate-review", s2_payload)
    scenarios.append(
        {
            "id": "S2",
            "name": "Task A Mixed Pidgin Persona",
            "endpoint": "/v1/simulate-review",
            "status": s2_status,
            "checks": {
                "has_llm_instrumentation": isinstance(s2_body, dict) and "llm_instrumentation" in s2_body,
                "context_reflected": isinstance(s2_body, dict)
                and (
                    "lagos" in str(s2_body.get("generated_review", "")).lower()
                    or "lagos" in str(s2_body.get("behavioural_basis", "")).lower()
                ),
                "no_mr_biggs_copy_leak": isinstance(s2_body, dict)
                and "abeg make dem upgrade this place" not in str(s2_body.get("generated_review", "")).lower(),
            },
            "response": s2_body,
        }
    )

    # Scenario 3: Task B cold start, no live data
    s3_payload = {
        "user_persona": {"user_id": "s3_cold", "review_history": []},
        "context": {"time_bucket": "evening", "entry_point": "food"},
        "n": 5,
        "enable_live_data": False,
    }
    s3_status, s3_body = _post("/v1/recommend", s3_payload)
    scenarios.append(
        {
            "id": "S3",
            "name": "Task B Cold Start No Live",
            "endpoint": "/v1/recommend",
            "status": s3_status,
            "checks": {
                "cold_start_handled": isinstance(s3_body, dict) and bool(s3_body.get("cold_start_handled")),
                "live_data_used_false": isinstance(s3_body, dict) and not bool(s3_body.get("live_data_used")),
                "has_explanations": isinstance(s3_body, dict)
                and all(bool(r.get("explanation")) for r in s3_body.get("recommendations", [])[:3]),
            },
            "response": s3_body,
        }
    )

    # Scenario 4: Task B personalized, no live data
    s4_payload = {
        "user_persona": {
            "user_id": "s4_personalized",
            "review_history": [
                {"item_name": "Jollof House", "item_category": "nigerian_cuisine", "rating": 5, "review_text": "Amazing jollof."},
                {"item_name": "Umu Okon", "item_category": "nigerian_cuisine", "rating": 4, "review_text": "Good local menu."},
                {"item_name": "Suya Spot", "item_category": "food", "rating": 4, "review_text": "Great taste."},
            ],
        },
        "context": {"time_bucket": "evening", "entry_point": "food", "region_tier": "urban"},
        "n": 5,
        "enable_live_data": False,
    }
    s4_status, s4_body = _post("/v1/recommend", s4_payload)
    scenarios.append(
        {
            "id": "S4",
            "name": "Task B Personalized No Live",
            "endpoint": "/v1/recommend",
            "status": s4_status,
            "checks": {
                "cold_start_handled_false": isinstance(s4_body, dict) and not bool(s4_body.get("cold_start_handled")),
                "live_data_used_false": isinstance(s4_body, dict) and not bool(s4_body.get("live_data_used")),
                "has_precision_items": isinstance(s4_body, dict)
                and any(r.get("recommendation_type") == "precision" for r in s4_body.get("recommendations", [])),
            },
            "response": s4_body,
        }
    )

    # Scenario 5: Task B personalized with live data on
    s5_payload = {
        "user_persona": {
            "user_id": "s5_live",
            "review_history": [
                {"item_name": "Jollof House", "item_category": "nigerian_cuisine", "rating": 5, "review_text": "Authentic taste."},
                {"item_name": "Palmwine Diner", "item_category": "food", "rating": 4, "review_text": "Worth it."},
            ],
        },
        "context": {"time_bucket": "evening", "entry_point": "food", "region_tier": "urban"},
        "n": 5,
        "enable_live_data": True,
        "live_results_limit": 3,
    }
    s5_status, s5_body = _post("/v1/recommend", s5_payload, timeout=90)
    scenarios.append(
        {
            "id": "S5",
            "name": "Task B Personalized With Live Data",
            "endpoint": "/v1/recommend",
            "status": s5_status,
            "checks": {
                "live_data_used_true": isinstance(s5_body, dict) and bool(s5_body.get("live_data_used")),
                "has_live_provider": isinstance(s5_body, dict) and bool(s5_body.get("live_search_provider")),
                "has_llm_instrumentation": isinstance(s5_body, dict) and isinstance(s5_body.get("llm_instrumentation"), dict),
            },
            "response": s5_body,
        }
    )

    # Scenario 6: Task B manual live query override
    s6_payload = {
        "user_persona": {"user_id": "s6_manual_query", "review_history": []},
        "context": {"time_bucket": "morning", "entry_point": "books", "region_tier": "urban"},
        "n": 5,
        "enable_live_data": True,
        "live_query": "best african fiction books 2026",
        "live_results_limit": 3,
    }
    s6_status, s6_body = _post("/v1/recommend", s6_payload, timeout=90)
    scenarios.append(
        {
            "id": "S6",
            "name": "Task B Manual Live Query Override",
            "endpoint": "/v1/recommend",
            "status": s6_status,
            "checks": {
                "manual_source": isinstance(s6_body, dict) and s6_body.get("live_search_source") == "manual",
                "query_echoed": isinstance(s6_body, dict) and bool(s6_body.get("live_search_query")),
                "live_data_used": isinstance(s6_body, dict) and bool(s6_body.get("live_data_used")),
            },
            "response": s6_body,
        }
    )

    # Scenario 7: Explain endpoint using latest recommendation from scenario 6
    rec_id = None
    if isinstance(s6_body, dict) and s6_body.get("recommendations"):
        rec_id = s6_body["recommendations"][0].get("recommendation_id")

    s7_payload = {
        "user_token": "s6_manual_query",
        "recommendation_id": rec_id or "rec_1_s6_manual_query",
    }
    s7_status, s7_body = _post("/v1/explain", s7_payload)
    scenarios.append(
        {
            "id": "S7",
            "name": "Task B Explain Trace",
            "endpoint": "/v1/explain",
            "status": s7_status,
            "checks": {
                "has_trace": isinstance(s7_body, dict) and bool(s7_body.get("trace")),
                "has_recommendation": isinstance(s7_body, dict) and isinstance(s7_body.get("recommendation"), dict),
            },
            "response": s7_body,
        }
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "scenarios": scenarios,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("# ARCHE Comprehensive Test Report (7 Scenarios)")
    lines.append("")
    lines.append(f"- Generated at (UTC): `{report['generated_at']}`")
    lines.append(f"- API Base URL: `{BASE_URL}`")
    lines.append("")

    passed = 0
    total_checks = 0

    for scenario in scenarios:
        lines.append(f"## {scenario['id']} - {scenario['name']}")
        lines.append(f"- Endpoint: `{scenario['endpoint']}`")
        lines.append(f"- HTTP Status: `{scenario['status']}`")
        checks = scenario.get("checks", {})
        for key, value in checks.items():
            total_checks += 1
            if value:
                passed += 1
            lines.append(f"- {key}: `{'PASS' if value else 'FAIL'}`")

        body = scenario.get("response")
        if isinstance(body, dict) and isinstance(body.get("recommendations"), list):
            top3 = body.get("recommendations", [])[:3]
            lines.append("- Top 3 recommendations:")
            for idx, rec in enumerate(top3, start=1):
                lines.append(
                    f"  - {idx}. `{rec.get('item_name')}` | type=`{rec.get('recommendation_type')}` | explanation=`{str(rec.get('explanation') or rec.get('reasoning') or '')[:140]}`"
                )
        elif isinstance(body, dict) and body.get("generated_review"):
            lines.append(f"- Predicted rating: `{body.get('predicted_rating')}`")
            lines.append(f"- Review excerpt: `{str(body.get('generated_review', ''))[:180]}`")
            lines.append(f"- LLM instrumentation: `{json.dumps(body.get('llm_instrumentation', {}))}`")
        elif isinstance(body, dict):
            lines.append(f"- Response excerpt: `{json.dumps(body)[:220]}`")
        else:
            lines.append(f"- Response excerpt: `{str(body)[:220]}`")

        lines.append("")

    lines.append("## Summary")
    lines.append(f"- Checks passed: `{passed}/{total_checks}`")
    lines.append(f"- Scenario count: `{len(scenarios)}`")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote report JSON: {JSON_PATH}")
    print(f"Wrote report MD: {REPORT_PATH}")
    print(f"Checks passed: {passed}/{total_checks}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
