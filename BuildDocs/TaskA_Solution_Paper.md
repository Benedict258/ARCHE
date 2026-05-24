# Task A Solution Paper — Simulated Reviews & Robust Input Handling

## Executive Summary

Task A for the DSN x BCT LLM Agent Challenge requires a judge-friendly endpoint that accepts varied inputs (structured JSON, malformed JSON, or free text) and returns a reproducible, structured simulated review that can be consumed by downstream systems and evaluated by judges. ARCHE's Task A implementation emphasizes input robustness, deterministic behavior when required, and high-quality LLM-driven review generation while preserving deterministic fallbacks for offline evaluation.

This paper documents the problem, approach, architecture, prompt patterns, API contract, evaluation plan, and operational considerations.

## Problem Statement

Judges will exercise the endpoint with messy inputs and expect consistent, testable outputs. The challenge is to reliably convert arbitrary text into a canonical review object, generate a high-quality review (summary, rating, body, tags), and expose results via a typed API that works in Swagger for manual judge testing.

Failure modes to mitigate:

- Invalid JSON / malformed payloads
- Ambiguous free-text inputs
- LLM variability and hallucination
- API latency due to external LLMs

## Objectives

- Accept free text and malformed JSON reliably and repair to a canonical schema.
- Produce a structured simulated review: `rating`, `summary`, `body`, and `reason_tags`.
- Provide `output_format` options (`json` or `text`) for automation or human judges.
- Ensure deterministic fallback behavior when LLMs are not available or for evaluation runs.

## System Architecture (Task A)

Key components (implemented in-repo):

- `api/request_repair.py`: multi-stage repair pipeline (parse → heuristic → LLM-normalize).
- `api/routes/task_a.py`: typed Pydantic request/response models exposed in Swagger.
- `agents/simulation_agent.py`: produces simulated behavioral snapshots used by review generator.
- `agents/review_generation_agent.py`: async LLM-based review generator with deterministic heuristic fallback.
- `memory/`: stores examples and last outputs for reproducibility.

Flow:

1. Client POSTs to `/v1/simulate-review` with either structured or raw `raw_input`.
2. `request_repair.repair_payload_from_text()` attempts JSON parse; if it fails, applies heuristics to extract fields; if still ambiguous, calls the LLM with a normalization prompt.
3. Normalized payload validated against the Task A Pydantic model.
4. `SimulationAgent` derives a behavioral snapshot (intent, affinities, exploration readiness).
5. `ReviewGenerationAgent.generate()` (async) produces the structured review.
6. Response returned in requested `output_format` and persisted for reproducibility.

## Prompting & Determinism

Prompt templates used for repair and review generation include explicit output format constraints (JSON schema) and few-shot examples to reduce hallucination. When reproducibility is required (auto tests), a deterministic fallback generates reviews using fixed templates and sampled cohort priors instead of LLM calls.

Example repair prompt (abbreviated):
"Convert the following free text into a JSON object with keys user_id, product_id, context, sentiment_notes. If data is missing, set explicit nulls. Respond with only valid JSON."

Example review generation template:
"Given simulation snapshot X and context Y, produce a JSON with `rating` (1-5), `summary` (<=20 words), `body` (1-3 sentences), and `reason_tags` (array). Output only JSON."

## API Contract (Task A)

- Endpoint: `POST /v1/simulate-review`
- Request fields: `raw_input` (string, optional), `user_persona` (object, optional), `context` (object), `output_format` (json|text)
- Response (json): `review` { `rating`, `summary`, `body`, `reason_tags` } or `text` blob when requested.

Swagger examples are embedded in `api/routes/task_a.py` for judge usability.

## Evaluation Plan

- Unit tests: malformed JSON and free-text repair success rate (automated in `tests/test_ingest.py`).
- Quality: human judge ratings on coherence, faithfulness, and usefulness.
- Consistency: deterministic fallback pass/fail across repeat runs.
- Latency: measure median time with LLM on and with deterministic fallback.

Metrics to report: repair success%, judged quality score (1–5), TTFB (ms).

## Operational Considerations

- `.env` keys for LLMs must be loaded at server start. For judges, we recommend `output_format=text` for simplicity and `enable_live_data=false` to keep runs deterministic.
- Rate-limits and timeouts enforced for LLM calls; fallback used on timeout.

## Risks & Mitigations

- LLM hallucination: constrain outputs to JSON-only prompts and validate before returning.
- Privacy: redact PII in `ingest` flow (deterministic hash-and-redact implemented in repo).

## Appendix: Files & Prompts

- `api/request_repair.py` — repair_payload_from_text()
- `api/routes/task_a.py` — endpoint + Pydantic models
- `agents/review_generation_agent.py` — prompt templates and async generate()

---

_(Task A draft prepared and aligned with the DSN x BCT Hack brief; ready for formatting.)_
