"""ARCHE Python SDK — Async client for ARCHE API."""

from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class IngestResponse:
    status: str
    privacy_mode: str
    user_token: str
    acknowledged_at: int


@dataclass
class BehavioralSnapshot:
    current_intent: str
    preference_cluster: str
    top_affinities: list[str]
    rejection_signals: list[str]
    engagement_mode: str
    exploration_readiness: float
    purchase_probability: float


@dataclass
class ContextModifiers:
    time_boosts: list[str]
    suppressed_categories: list[str]
    active_context: str


@dataclass
class SimulationResponse:
    user_token: str
    behavioral_snapshot: BehavioralSnapshot
    context_modifiers: ContextModifiers
    cold_start_confidence: float
    simulation_basis: str
    memory_sources: list[str]


@dataclass
class Recommendation:
    recommendation_id: str
    item_name: str
    item_category: str
    confidence: float
    recommendation_type: str
    exploration_factor: str
    explanation: str


@dataclass
class RecommendationSet:
    user_token: str
    simulation_basis: str
    recommendations: list[Recommendation]


class ArcheClient:
    """Async Python client for ARCHE API.

    Usage:
        client = ArcheClient("http://127.0.0.1:8000")
        ingest_resp = await client.ingest("user_123", {"event_type": "click"})
        sim_resp = await client.simulate("user_123")
        rec_resp = await client.recommend("user_123")
    """

    def __init__(self, api_base_url: str = "http://127.0.0.1:8000"):
        self.api_base_url = api_base_url.rstrip("/")

    async def ingest(self, user_token: str, signal: Dict[str, Any]) -> IngestResponse:
        """Post a behavioral signal for ingestion.

        Args:
            user_token: User identifier
            signal: Behavioral signal dict with event_type, item_token, item_category, etc.

        Returns:
            IngestResponse with anonymized token and acknowledged_at timestamp
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/ingest",
                    json={"user_token": user_token, "signal": signal},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                return IngestResponse(
                    status=data["status"],
                    privacy_mode=data["privacy_mode"],
                    user_token=data["user_token"],
                    acknowledged_at=data["acknowledged_at"],
                )
        except Exception as e:
            raise RuntimeError(f"Ingest failed: {str(e)}")

    async def simulate(
        self, user_token: str, context: Dict[str, Any] | None = None
    ) -> SimulationResponse:
        """Run user behavioral simulation.

        Args:
            user_token: User identifier
            context: Optional contextual modifiers (time_bucket, device_class, entry_point, etc.)

        Returns:
            SimulationResponse with behavioral snapshot, context modifiers, and basis
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/simulate",
                    json={"user_token": user_token, "context": context or {}},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                snapshot = data.get("behavioral_snapshot", {})
                modifiers = data.get("context_modifiers", {})
                return SimulationResponse(
                    user_token=data.get("user_token"),
                    behavioral_snapshot=BehavioralSnapshot(
                        current_intent=snapshot.get("current_intent"),
                        preference_cluster=snapshot.get("preference_cluster"),
                        top_affinities=snapshot.get("top_affinities", []),
                        rejection_signals=snapshot.get("rejection_signals", []),
                        engagement_mode=snapshot.get("engagement_mode"),
                        exploration_readiness=snapshot.get("exploration_readiness", 0.0),
                        purchase_probability=snapshot.get("purchase_probability", 0.0),
                    ),
                    context_modifiers=ContextModifiers(
                        time_boosts=modifiers.get("time_boosts", []),
                        suppressed_categories=modifiers.get("suppressed_categories", []),
                        active_context=modifiers.get("active_context", ""),
                    ),
                    cold_start_confidence=data.get("cold_start_confidence", 0.0),
                    simulation_basis=data.get("simulation_basis", ""),
                    memory_sources=data.get("memory_sources", []),
                )
        except Exception as e:
            raise RuntimeError(f"Simulate failed: {str(e)}")

    async def recommend(
        self, user_token: str, context: Dict[str, Any] | None = None, n: int = 10
    ) -> RecommendationSet:
        """Get ranked recommendations using simulation output.

        Args:
            user_token: User identifier
            context: Optional contextual modifiers
            n: Number of recommendations to return (default 10)

        Returns:
            RecommendationSet with ranked recommendations and basis
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/recommend",
                    json={"user_token": user_token, "context": context or {}, "n": n},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                recs = [
                    Recommendation(
                        recommendation_id=r["recommendation_id"],
                        item_name=r["item_name"],
                        item_category=r["item_category"],
                        confidence=r["confidence"],
                        recommendation_type=r["recommendation_type"],
                        exploration_factor=r["exploration_factor"],
                        explanation=r["explanation"],
                    )
                    for r in data.get("recommendations", [])
                ]
                return RecommendationSet(
                    user_token=data.get("user_token"),
                    simulation_basis=data.get("simulation_basis"),
                    recommendations=recs,
                )
        except Exception as e:
            raise RuntimeError(f"Recommend failed: {str(e)}")

    async def explain(self, user_token: str, recommendation_id: str) -> Dict[str, Any]:
        """Get full causal explanation for a recommendation.

        Args:
            user_token: User identifier
            recommendation_id: ID of the recommendation to explain

        Returns:
            Explanation response with trace, alternatives, and simulation snapshot
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/explain",
                    json={"user_token": user_token, "recommendation_id": recommendation_id},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise RuntimeError(f"Explain failed: {str(e)}")

    async def health(self) -> Dict[str, str]:
        """Check API health.

        Returns:
            Health status dict
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/v1/health", timeout=5.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise RuntimeError(f"Health check failed: {str(e)}")
