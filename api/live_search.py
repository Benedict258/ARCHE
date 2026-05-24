from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from agents.simulation_agent import SimulationAgent


@dataclass
class LiveSearchResult:
    item_id: str
    item_name: str
    item_category: str
    source: str = "serper"
    description: str = ""
    price_tier: str = "mid"
    url: str | None = None
    metadata: dict[str, Any] | None = None


class LiveSearchService:
    """LLM-guided live web search helper for recommendation candidates.

    Uses Serper as the live search backend and the configured LLM to refine
    the search query when available.
    """

    def __init__(self) -> None:
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.serper_base_url = os.getenv("SERPER_BASE_URL", "https://google.serper.dev/search")
        self.llm_agent = SimulationAgent()

    def available(self) -> bool:
        return bool(self.serper_api_key)

    @staticmethod
    def _slug(text: str) -> str:
        cleaned = " ".join((text or "").strip().lower().split())
        return cleaned.replace(" ", "_")[:40] or "live_item"

    @staticmethod
    def _fingerprint(text: str) -> str:
        return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]

    async def build_query(
        self,
        *,
        category: str | None,
        context: dict[str, Any] | None,
        user_history: list[dict[str, Any]] | None,
        live_query: str | None = None,
    ) -> dict[str, str]:
        """Use the LLM to refine a search query when possible."""
        if live_query and live_query.strip():
            return {"source": "manual", "query": live_query.strip(), "category": (category or "general").strip() or "general"}

        category = (category or "general").strip() or "general"
        context = context or {}
        if self.llm_agent.llm is None:
            city = str(context.get("region") or context.get("region_tier") or "Nigeria").strip()
            if category in {"food", "restaurant", "restaurants", "nigerian_cuisine"}:
                query = f"best {category} in {city}"
            elif category in {"books", "fiction", "literature"}:
                query = f"best {category} recommendations"
            else:
                query = f"top {category} recommendations"
            return {"source": "heuristic", "query": query, "category": category}

        history_snippet = ""
        if user_history:
            sample = user_history[:3]
            history_snippet = json.dumps(sample, ensure_ascii=False)

        system_prompt = (
            "You are a live search planner for ARCHE. Return ONLY JSON with keys: "
            "query, category, source. Create a concise web search query that will find current, real, useful options."
        )
        user_prompt = (
            f"Target category: {category}\n"
            f"Context: {json.dumps(context, ensure_ascii=False)}\n"
            f"Recent history: {history_snippet}\n"
            "Return a search query suitable for Serper web search."
        )
        try:
            content = await self.llm_agent.call_llm(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.1)
            parsed = json.loads(content)
            if isinstance(parsed, dict) and parsed.get("query"):
                return {
                    "source": str(parsed.get("source") or "llm").strip() or "llm",
                    "query": str(parsed.get("query")).strip(),
                    "category": str(parsed.get("category") or category).strip() or category,
                }
        except Exception:
            pass

        city = str(context.get("region") or context.get("region_tier") or "Nigeria").strip()
        query = f"best {category} in {city}"
        return {"source": "fallback", "query": query, "category": category}

    async def search(self, query: str, num_results: int = 10) -> list[LiveSearchResult]:
        if not self.serper_api_key:
            return []

        payload = {"q": query, "num": max(1, min(int(num_results), 10))}
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(self.serper_base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        organic = data.get("organic") or []
        results: list[LiveSearchResult] = []
        inferred_category = self._infer_category(query)
        for idx, item in enumerate(organic[:num_results], start=1):
            title = str(item.get("title") or item.get("snippet") or f"live_item_{idx}")
            link = str(item.get("link") or "")
            snippet = str(item.get("snippet") or "")
            results.append(
                LiveSearchResult(
                    item_id=f"live:{self._fingerprint(title + link)}",
                    item_name=title,
                    item_category=inferred_category,
                    source="serper",
                    description=snippet,
                    price_tier="mid",
                    url=link or None,
                    metadata={"position": idx, "query": query},
                )
            )
        return results

    @staticmethod
    def _infer_category(query: str) -> str:
        text = query.lower()
        if any(token in text for token in ["restaurant", "food", "dining", "eat", "meal", "cafe", "hotel"]):
            return "food"
        if any(token in text for token in ["book", "novel", "read", "goodreads", "literature"]):
            return "books"
        if any(token in text for token in ["shop", "product", "amazon", "buy", "store", "shopping"]):
            return "shopping"
        return "general"

    def merge_with_local_catalog(
        self,
        live_items: list[LiveSearchResult],
        local_catalog: list[dict[str, Any]],
        *,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in live_items:
            if item.item_id in seen:
                continue
            seen.add(item.item_id)
            merged.append(
                {
                    "item_id": item.item_id,
                    "item_name": item.item_name,
                    "item_category": item.item_category,
                    "source": item.source,
                    "description": item.description,
                    "price_tier": item.price_tier,
                    "url": item.url,
                    "metadata": item.metadata or {},
                }
            )
            if len(merged) >= limit:
                return merged

        for item in local_catalog:
            key = str(item.get("item_id") or item.get("key") or item.get("item_name") or "")
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "item_id": item.get("item_id") or item.get("key"),
                    "item_name": item.get("item_name") or item.get("item_id") or item.get("key") or "item",
                    "item_category": item.get("item_category") or "general",
                    "source": item.get("source") or "local_catalog",
                    "description": item.get("description") or "",
                    "price_tier": item.get("price_tier") or "mid",
                    "metadata": item.get("metadata") or {},
                }
            )
            if len(merged) >= limit:
                break

        return merged
