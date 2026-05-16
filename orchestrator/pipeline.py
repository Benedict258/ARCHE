"""ARCHE orchestrator pipeline using LangGraph for sequential step execution."""

from typing import Any, Dict
from dataclasses import dataclass, field


@dataclass
class PipelineState:
    """Shared state across pipeline steps."""
    user_token: str
    ingest_signal: Dict[str, Any] | None = None
    ingest_response: Dict[str, Any] | None = None
    simulation_context: Dict[str, Any] | None = None
    simulation_response: Dict[str, Any] | None = None
    recommendation_context: Dict[str, Any] = field(default_factory=dict)
    recommendation_response: Dict[str, Any] | None = None
    explain_request: Dict[str, Any] | None = None
    explain_response: Dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)


class ArchePipeline:
    """Lightweight orchestrator for ARCHE pipeline without external dependencies.

    Supports sequential execution of ingest -> simulate -> recommend -> explain.
    Can be extended to use LangGraph for full async/state management later.
    """

    def __init__(self, api_base_url: str = "http://127.0.0.1:8000"):
        self.api_base_url = api_base_url

    async def execute_full_flow(
        self, user_token: str, signal: Dict[str, Any], context: Dict[str, Any] | None = None
    ) -> PipelineState:
        """Execute full pipeline: ingest → simulate → recommend.

        Args:
            user_token: User identifier
            signal: Behavioral signal for ingestion
            context: Optional contextual modifiers for simulation

        Returns:
            Final PipelineState with all responses
        """
        state = PipelineState(
            user_token=user_token,
            ingest_signal=signal,
            simulation_context=context or {},
        )

        try:
            # Step 1: Ingest
            state = await self._step_ingest(state)
            if state.errors:
                return state

            # Step 2: Simulate
            state = await self._step_simulate(state)
            if state.errors:
                return state

            # Step 3: Recommend
            state = await self._step_recommend(state)
            if state.errors:
                return state

        except Exception as e:
            state.errors.append(f"Pipeline error: {str(e)}")

        return state

    async def _step_ingest(self, state: PipelineState) -> PipelineState:
        """Execute ingest step."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/ingest",
                    json={
                        "user_token": state.user_token,
                        "signal": state.ingest_signal,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    state.ingest_response = response.json()
                else:
                    state.errors.append(f"Ingest failed: {response.status_code}")
        except Exception as e:
            state.errors.append(f"Ingest error: {str(e)}")
        return state

    async def _step_simulate(self, state: PipelineState) -> PipelineState:
        """Execute simulate step."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/simulate",
                    json={
                        "user_token": state.user_token,
                        "context": state.simulation_context,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    state.simulation_response = response.json()
                else:
                    state.errors.append(f"Simulate failed: {response.status_code}")
        except Exception as e:
            state.errors.append(f"Simulate error: {str(e)}")
        return state

    async def _step_recommend(self, state: PipelineState) -> PipelineState:
        """Execute recommend step using simulation output."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/recommend",
                    json={
                        "user_token": state.user_token,
                        "context": state.simulation_context,
                        "n": 10,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    state.recommendation_response = response.json()
                else:
                    state.errors.append(f"Recommend failed: {response.status_code}")
        except Exception as e:
            state.errors.append(f"Recommend error: {str(e)}")
        return state

    async def _step_explain(self, state: PipelineState, recommendation_id: str) -> PipelineState:
        """Execute explain step for a specific recommendation."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/explain",
                    json={
                        "user_token": state.user_token,
                        "recommendation_id": recommendation_id,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    state.explain_response = response.json()
                else:
                    state.errors.append(f"Explain failed: {response.status_code}")
        except Exception as e:
            state.errors.append(f"Explain error: {str(e)}")
        return state
