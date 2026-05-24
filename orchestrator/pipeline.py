"""ARCHE orchestrator pipeline representing the agent loop pattern.

The orchestrator executes the agentic reasoning sequence:
1. THINK: Evaluate intent, task, and active context.
2. RETRIEVE: Fetch user memory and cohort priors.
3. SIMULATE: Run user brain-state simulation (behavioral snapshot).
4. REASON: Inject context modifiers, price sensitivity, and category boosts.
5. ACT: Execute review simulation (Task A) or personalized ranking (Task B).
6. EXPLAIN: Generate causal reasoning traces for all outputs.
"""

from typing import Any, Dict
from dataclasses import dataclass, field


@dataclass
class PipelineState:
    """Shared state across the agent pipeline steps."""
    user_token: str
    ingest_signal: Dict[str, Any] | None = None
    ingest_response: Dict[str, Any] | None = None
    simulation_context: Dict[str, Any] | None = None
    simulation_response: Dict[str, Any] | None = None
    recommendation_response: Dict[str, Any] | None = None
    explain_response: Dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)


class ArchePipeline:
    """Agentic pipeline orchestrator for ARCHE.

    Coordinates the agent sequence (Retrieve -> Simulate -> Act -> Explain)
    via API calls or internal service state.
    """

    def __init__(self, api_base_url: str = "http://127.0.0.1:8000"):
        self.api_base_url = api_base_url

    async def execute_full_flow(
        self, user_token: str, signal: Dict[str, Any], context: Dict[str, Any] | None = None
    ) -> PipelineState:
        """Execute full agent pipeline: Ingest (Retrieve) → Simulate → Recommend (Act) → Explain.

        Args:
            user_token: User identifier
            signal: Behavioral signal for ingestion
            context: Optional contextual modifiers for simulation

        Returns:
            Final PipelineState with all responses and reasoning logs
        """
        state = PipelineState(
            user_token=user_token,
            ingest_signal=signal,
            simulation_context=context or {},
        )

        try:
            # Step 1: RETRIEVE / INGEST (Update memory layer with new signal)
            state = await self._retrieve_and_ingest(state)
            if state.errors:
                return state

            # Step 2: SIMULATE (Build dynamic behavioral snapshot)
            state = await self._simulate_user_state(state)
            if state.errors:
                return state

            # Step 3: ACT (Generate context-aware recommendations)
            state = await self._act_recommend(state)
            if state.errors:
                return state

            # Step 4: EXPLAIN (Provide causal reasoning traces for top items)
            state = await self._explain_outputs(state)

        except Exception as e:
            state.errors.append(f"Pipeline execution error: {str(e)}")

        return state

    async def _retrieve_and_ingest(self, state: PipelineState) -> PipelineState:
        """Step 1: Retrieve and Ingest signal to update persistent memory."""
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
                if response.status_code in (200, 201):
                    state.ingest_response = response.json()
                else:
                    state.errors.append(f"Retrieve/Ingest failed: {response.status_code}")
        except Exception as e:
            state.errors.append(f"Retrieve/Ingest error: {str(e)}")
        return state

    async def _simulate_user_state(self, state: PipelineState) -> PipelineState:
        """Step 2: Simulate the user's forward-looking cognitive/behavioral state."""
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
                    state.errors.append(f"User state simulation failed: {response.status_code}")
        except Exception as e:
            state.errors.append(f"User state simulation error: {str(e)}")
        return state

    async def _act_recommend(self, state: PipelineState) -> PipelineState:
        """Step 3: Act by generating personalized recommendations grounded in simulation."""
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
                    state.errors.append(f"Act/Recommend failed: {response.status_code}")
        except Exception as e:
            state.errors.append(f"Act/Recommend error: {str(e)}")
        return state

    async def _explain_outputs(self, state: PipelineState) -> PipelineState:
        """Step 4: Explain by generating causal reasoning traces for top recommended items."""
        try:
            recs = (state.recommendation_response or {}).get("recommendations") or []
            if not recs:
                return state

            # Explain the top recommendation to build the primary trace
            top_rec = recs[0]
            rec_id = top_rec.get("recommendation_id")
            if not rec_id:
                return state

            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/explain",
                    json={
                        "user_token": state.user_token,
                        "recommendation_id": rec_id,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    state.explain_response = response.json()
                else:
                    state.errors.append(f"Explain query failed: {response.status_code}")
        except Exception as e:
            state.errors.append(f"Explain query error: {str(e)}")
        return state

