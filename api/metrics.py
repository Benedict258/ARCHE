"""Prometheus metrics for ARCHE.

Self-hosted, account-free: exposes `/metrics` in Prometheus text-exposition
format. Nothing scrapes it yet by default (no Prometheus/Grafana service is
declared in docker-compose.yml) — that's an operational choice for whoever
deploys this, not something to provision speculatively here.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "arche_http_requests_total",
    "Total HTTP requests handled",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "arche_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)

llm_calls_total = Counter(
    "arche_llm_calls_total",
    "Total LLM provider calls",
    ["provider", "operation", "outcome"],
)

embedding_calls_total = Counter(
    "arche_embedding_calls_total",
    "Total embedding provider calls",
    ["provider", "outcome"],
)

live_search_calls_total = Counter(
    "arche_live_search_calls_total",
    "Total live web search calls",
    ["provider", "outcome"],
)
