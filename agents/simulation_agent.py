from __future__ import annotations

import json
import os
from typing import Any

import httpx

from .base_agent import BaseAgent, AgentState


class SimulationAgent(BaseAgent):
    """Simulates the user's BRAIN-STATE from memory and context signals using LLM reasoning.
    
    This agent goes beyond predictive models to simulate actual behavioral patterns,
    cognitive biases, and decision-making processes. It reasons over:
    - User's past behavior and affinity patterns
    - Current contextual signals (time, device, region)
    - Population cohort behavioral priors
    - Language register and communication patterns
    
    Output: A behavioral snapshot representing the user's simulated mental state.
    """

    name = "simulation"

    def __init__(self):
        self.llm = None
        self.llm_provider = None
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        self._init_llm()

    def _init_llm(self):
        """Initialize provider chain for behavior simulation.

        Priority:
        1) Explicit provider via LLM_PROVIDER
        2) Groq Chat Completions API (OpenAI-compatible endpoint)
        3) Anthropic (only if Groq is unavailable and the key is present)
        4) Deterministic heuristic fallback
        """
        provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()

        if provider == "groq" and self.groq_api_key:
            self.llm = "groq"
            self.llm_provider = "groq"
            return

        if provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=api_key)
                    self.llm_provider = "anthropic"
                    return
            except ImportError:
                self.llm = None

        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            ChatAnthropic = None

        if self.groq_api_key:
            self.llm = "groq"
            self.llm_provider = "groq"
            return

        if ChatAnthropic is not None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=api_key)
                self.llm_provider = "anthropic"
                return

        self.llm = None
        self.llm_provider = None

    async def run(self, state: AgentState) -> AgentState:
        """Execute the simulation agent node in the LangGraph."""
        # TODO: Wire state updates through the graph
        return state

    async def simulate_brain_state(self, user_token: str, memory_payload: dict[str, Any], 
                                   context: dict[str, Any]) -> dict[str, Any]:
        """Simulate the user's cognitive/behavioral state.
        
        Args:
            user_token: User identifier hash
            memory_payload: User's interaction history from memory layer
            context: Current contextual signals (time, device, region, etc.)
            
        Returns:
            Behavioral snapshot: current_intent, preference_cluster, affinities, 
            rejection_signals, engagement_mode, exploration_readiness, purchase_probability
        """
        
        if not self.llm:
            # Fallback to heuristic simulation
            return self._fallback_simulate(user_token, memory_payload, context)
        
        # Build LLM-driven behavior simulation prompt
        system_prompt = """You are ARCHE's Behavior Simulation Engine.

Your job is to simulate a user's BRAIN STATE given their interaction history and current context.
You are not predicting behavior—you are simulating their cognitive state, decision-making process, 
and behavioral patterns.

Consider:
1. Past behavioral patterns and affinities
2. Cognitive biases and decision heuristics evident in their history
3. Current contextual state (time, device, environment)
4. Risk tolerance, exploration readiness, purchase likelihood
5. Language/communication register they use

Output ONLY valid JSON matching this schema:
{
  "current_intent": "exploratory_browsing | active_purchase | research | entertainment | social",
  "preference_cluster": "A | B | C | D | E",
  "top_affinities": ["category1", "category2", "category3"],
  "rejection_signals": ["category_disliked1", "category_disliked2"],
  "engagement_mode": "high_depth | scanning | quick_check",
  "exploration_readiness": 0.0-1.0,
  "purchase_probability": 0.0-1.0,
  "behavioral_basis": "brief one-sentence reasoning"
}"""

        user_prompt = f"""User interaction history:
{json.dumps(memory_payload, indent=2)}

Current context:
{json.dumps(context, indent=2)}

Simulate this user's brain state. What is their current intent? 
What are they ready to explore? What will they reject?
Return only JSON."""

        try:
            if self.llm_provider == "anthropic":
                response = await self.llm.ainvoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ])
                content = response.content
            elif self.llm_provider == "groq":
                content = await self._simulate_with_groq(system_prompt=system_prompt, user_prompt=user_prompt)
            else:
                return self._fallback_simulate(user_token, memory_payload, context)

            if isinstance(content, str):
                if "```json" in content:
                    content = content.split("```json", 1)[1].split("```", 1)[0]
                elif "```" in content:
                    content = content.split("```", 1)[1].split("```", 1)[0]
                snapshot = json.loads(content.strip())
            else:
                snapshot = content

            return self._normalize_snapshot(snapshot)

        except Exception as e:
            # Fallback to heuristic if LLM fails
            print(f"LLM simulation failed: {e}, falling back to heuristic")
            return self._fallback_simulate(user_token, memory_payload, context)

    async def call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """General-purpose LLM call used by other agents.

        IMPORTANT: Intentionally does NOT enforce token limits. Caller is responsible.
        Returns the raw string content from the LLM.
        """
        if not self.llm:
            raise RuntimeError("No LLM provider configured")

        # Anthropic via langchain wrapper
        if self.llm_provider == "anthropic":
            response = await self.llm.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ])
            return getattr(response, "content", str(response))

        # Groq direct HTTP call
        if self.llm_provider == "groq":
            return await self._call_groq(system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature)

        raise RuntimeError("Unsupported LLM provider")

    async def _call_groq(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("Groq response has no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise RuntimeError("Groq response has empty message content")
        return str(content)

    async def _simulate_with_groq(self, system_prompt: str, user_prompt: str) -> str:
        if not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("Groq response has no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise RuntimeError("Groq response has empty message content")
        return str(content)

    @staticmethod
    def _normalize_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
        """Ensure snapshot conforms to expected schema."""
        return {
            "current_intent": snapshot.get("current_intent", "exploratory_browsing"),
            "preference_cluster": snapshot.get("preference_cluster", "A"),
            "top_affinities": snapshot.get("top_affinities", []),
            "rejection_signals": snapshot.get("rejection_signals", []),
            "engagement_mode": snapshot.get("engagement_mode", "scanning"),
            "exploration_readiness": float(snapshot.get("exploration_readiness", 0.5)),
            "purchase_probability": float(snapshot.get("purchase_probability", 0.3)),
            "behavioral_basis": snapshot.get("behavioral_basis", ""),
        }

    @staticmethod
    def _fallback_simulate(user_token: str, memory_payload: dict[str, Any],
                          context: dict[str, Any]) -> dict[str, Any]:
        """Heuristic fallback when LLM is unavailable."""
        # Extract signals from memory
        event_count = len(memory_payload.get("events", []))
        categories = set()
        total_engagement = 0.0
        
        for event in memory_payload.get("events", []):
            if "item_category" in event:
                categories.add(event["item_category"])
            if "engagement_depth" in event:
                total_engagement += event["engagement_depth"]
        
        avg_engagement = total_engagement / max(1, event_count)
        
        # Simple heuristic rules
        if event_count == 0:
            intent = "exploratory_browsing"
            exploration_readiness = 0.9
            purchase_prob = 0.2
        elif avg_engagement > 0.7:
            intent = "active_purchase"
            exploration_readiness = 0.4
            purchase_prob = 0.7
        else:
            intent = "research"
            exploration_readiness = 0.6
            purchase_prob = 0.4
        
        return {
            "current_intent": intent,
            "preference_cluster": "A",
            "top_affinities": list(categories)[:3],
            "rejection_signals": [],
            "engagement_mode": "high_depth" if avg_engagement > 0.6 else "scanning",
            "exploration_readiness": min(1.0, exploration_readiness),
            "purchase_probability": min(1.0, purchase_prob),
            "behavioral_basis": f"Heuristic fallback: {event_count} events, avg engagement {avg_engagement:.2f}",
        }

    @staticmethod
    def simulate(user_token: str, context: Any, memory_payload: dict[str, Any]):
        """Legacy sync interface for backward compatibility."""
        from api.main import _build_simulation_response
        return _build_simulation_response(user_token, context, memory_payload)
