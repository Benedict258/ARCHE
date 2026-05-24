from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base_agent import BaseAgent, AgentState


@dataclass
class ContextSummary:
    time_bucket: str
    day_type: str
    device_class: str
    network_quality: str
    region_tier: str
    session_depth: int
    entry_point: str
    active_context: str
    time_boosts: list[str]
    suppressed_categories: list[str]


class ContextAgent(BaseAgent):
    """Normalizes the request context into agent-readable signals."""

    name = "context"

    @staticmethod
    def normalize(context: dict[str, Any] | None) -> ContextSummary:
        context = context or {}
        time_bucket = str(
            context.get("time_bucket")
            or context.get("time_of_day")
            or context.get("time")
            or "unspecified"
        )
        day_type = str(context.get("day_type") or context.get("day") or "unspecified")
        device_class = str(context.get("device_class") or context.get("device") or "unspecified")
        network_quality = str(context.get("network_quality") or context.get("network") or "medium")
        region_tier = str(
            context.get("region_tier")
            or context.get("location_tier")
            or context.get("region")
            or context.get("location")
            or "unspecified"
        )
        session_depth = int(context.get("session_depth") or context.get("depth") or 0)
        entry_point = str(context.get("entry_point") or context.get("occasion") or "direct")

        time_boosts = [time_bucket] if time_bucket != "unspecified" else []
        if device_class != "unspecified":
            time_boosts.append(f"device:{device_class}")

        suppressed_categories: list[str] = []
        if network_quality == "low":
            suppressed_categories.append("heavy_media")
        if entry_point == "notification":
            suppressed_categories.append("deep_research")

        active_context = ", ".join(
            [
                time_bucket,
                day_type,
                device_class,
                network_quality,
                region_tier,
                entry_point,
            ]
        )
        return ContextSummary(
            time_bucket=time_bucket,
            day_type=day_type,
            device_class=device_class,
            network_quality=network_quality,
            region_tier=region_tier,
            session_depth=session_depth,
            entry_point=entry_point,
            active_context=active_context,
            time_boosts=time_boosts,
            suppressed_categories=suppressed_categories,
        )

    async def run(self, state: AgentState) -> AgentState:
        return state
