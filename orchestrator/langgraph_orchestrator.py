"""ARCHE LangGraph-based multi-agent orchestrator.

This module implements a true agentic architecture using LangGraph where:
- Each agent is a specialized LLM-powered node in a DAG
- State flows through the graph: retrieval → simulation → recommendation → explanation
- Agents reason over user memory, behavioral patterns, and contextual signals
- The system simulates user BRAIN states, not just predicts behavior
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

try:
    from langgraph.graph import StateGraph
    from langchain_anthropic import ChatAnthropic
except ImportError:
    StateGraph = None
    ChatAnthropic = None


@dataclass
class GraphState:
    """Shared state flowing through the LangGraph DAG."""
    
    user_token: str
    context: dict[str, Any] = field(default_factory=dict)
    
    # Retrieval phase output
    memory_payload: dict[str, Any] | None = None
    candidate_items: list[dict[str, Any]] = field(default_factory=list)
    
    # Simulation phase output
    behavioral_snapshot: dict[str, Any] | None = None
    simulation_basis: str = ""
    
    # Recommendation phase output
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    exploration_ratio: float = 0.0
    
    # Explanation phase output
    explanation_traces: dict[str, Any] = field(default_factory=dict)
    
    # Error tracking
    errors: list[str] = field(default_factory=list)


class LangGraphOrchestrator:
    """Multi-agent orchestrator using LangGraph for agentic reasoning and execution."""
    
    def __init__(self):
        self.graph = None
        self.compiled_graph = None
        self._init_graph()
    
    def _init_graph(self):
        """Initialize the LangGraph state graph with agent nodes."""
        if StateGraph is None:
            print("Warning: LangGraph not installed, falling back to sequential execution")
            return
        
        # Define the state graph
        graph_builder = StateGraph(GraphState)
        
        # Add nodes
        graph_builder.add_node("retrieval", self._node_retrieval)
        graph_builder.add_node("simulation", self._node_simulation)
        graph_builder.add_node("recommendation", self._node_recommendation)
        graph_builder.add_node("explanation", self._node_explanation)
        
        # Define edges/routing
        graph_builder.set_entry_point("retrieval")
        graph_builder.add_edge("retrieval", "simulation")
        graph_builder.add_edge("simulation", "recommendation")
        graph_builder.add_edge("recommendation", "explanation")
        graph_builder.set_finish_point("explanation")
        
        self.graph = graph_builder
        self.compiled_graph = graph_builder.compile()
    
    async def orchestrate(self, user_token: str, context: dict[str, Any] | None = None) -> GraphState:
        """Run the full agentic pipeline.
        
        Args:
            user_token: User identifier hash
            context: Contextual signals (time, device, region, etc.)
        
        Returns:
            Final GraphState with all pipeline outputs
        """
        initial_state = GraphState(
            user_token=user_token,
            context=context or {}
        )
        
        if self.compiled_graph is None:
            # Fall back to sequential if LangGraph not available
            return await self._sequential_pipeline(initial_state)
        
        # Execute the graph
        try:
            final_state = await self.compiled_graph.ainvoke(initial_state)
            return final_state
        except Exception as e:
            initial_state.errors.append(f"Graph execution failed: {str(e)}")
            return await self._sequential_pipeline(initial_state)
    
    async def _sequential_pipeline(self, state: GraphState) -> GraphState:
        """Fallback sequential execution when LangGraph is unavailable."""
        state = await self._node_retrieval(state)
        if state.errors:
            return state
        state = await self._node_simulation(state)
        if state.errors:
            return state
        state = await self._node_recommendation(state)
        if state.errors:
            return state
        state = await self._node_explanation(state)
        return state
    
    @staticmethod
    async def _node_retrieval(state: GraphState) -> GraphState:
        """Retrieval node: Fetch user memory and candidate items."""
        try:
            from memory.memory_manager import MemoryManager
            
            memmgr = MemoryManager()
            memory = memmgr.retrieve_all(state.user_token) if hasattr(memmgr.retrieve_all, '__call__') else {}
            
            state.memory_payload = memory or {}
            
            # Load candidate items from dataset
            from data.dataset_loader import UnifiedDatasetLoader
            loader = UnifiedDatasetLoader()
            
            # For MVP, get sample from Yelp if available
            try:
                yelp_items = loader.load_yelp_catalog(limit=100)
                state.candidate_items = yelp_items
            except:
                # Fall back to mock data
                state.candidate_items = []
            
        except Exception as e:
            state.errors.append(f"Retrieval failed: {str(e)}")
        
        return state
    
    @staticmethod
    async def _node_simulation(state: GraphState) -> GraphState:
        """Simulation node: Simulate user brain state from memory and context."""
        try:
            from agents.simulation_agent import SimulationAgent
            
            agent = SimulationAgent()
            snapshot = await agent.simulate_brain_state(
                user_token=state.user_token,
                memory_payload=state.memory_payload or {},
                context=state.context
            )
            
            state.behavioral_snapshot = snapshot
            state.simulation_basis = snapshot.get("behavioral_basis", "LLM simulation")
            
        except Exception as e:
            state.errors.append(f"Simulation failed: {str(e)}")
        
        return state
    
    @staticmethod
    async def _node_recommendation(state: GraphState) -> GraphState:
        """Recommendation node: Rank candidates using simulation state."""
        try:
            if not state.behavioral_snapshot or not state.candidate_items:
                state.recommendations = []
                return state
            
            from agents.recommendation_agent import RecommendationAgent
            
            recommendations = RecommendationAgent.rank_candidates(
                candidates=state.candidate_items,
                simulation=type('obj', (object,), {'behavioral_snapshot': state.behavioral_snapshot})(),
                context=state.context
            )
            
            state.recommendations = recommendations
            state.exploration_ratio = RecommendationAgent.calculate_exploration_ratio(recommendations)
            
        except Exception as e:
            state.errors.append(f"Recommendation failed: {str(e)}")
        
        return state
    
    @staticmethod
    async def _node_explanation(state: GraphState) -> GraphState:
        """Explanation node: Generate causal reasoning traces for recommendations."""
        try:
            if not state.recommendations:
                state.explanation_traces = {}
                return state
            
            from agents.explainability_agent import ExplainabilityAgent
            
            traces = {}
            for rec in state.recommendations[:5]:  # Explain top 5
                trace = ExplainabilityAgent.generate_reasoning_trace(
                    recommendation=rec,
                    simulation=state.behavioral_snapshot,
                    context=state.context
                )
                traces[rec.get("recommendation_id", "unknown")] = trace
            
            state.explanation_traces = traces
            
        except Exception as e:
            state.errors.append(f"Explanation failed: {str(e)}")
        
        return state


async def test_orchestrator():
    """Quick test of the orchestrator."""
    orch = LangGraphOrchestrator()
    
    state = await orch.orchestrate(
        user_token="test_user_123",
        context={
            "time_bucket": "evening",
            "device_class": "mobile",
            "region_tier": "urban"
        }
    )
    
    print(f"Pipeline completed with {len(state.errors)} errors")
    print(f"Behavioral snapshot: {state.behavioral_snapshot}")
    print(f"Recommendations: {len(state.recommendations)}")
    
    return state


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_orchestrator())
