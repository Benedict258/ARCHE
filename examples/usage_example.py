"""Example usage of ARCHE SDK and Orchestrator."""

import asyncio
from sdk.client import ArcheClient
from orchestrator.pipeline import ArchePipeline


async def example_sdk_usage():
    """Example of using the ARCHE SDK directly."""
    client = ArcheClient("http://127.0.0.1:8000")

    try:
        # Check health
        health = await client.health()
        print(f"API Health: {health}")

        # Ingest a signal
        ingest_resp = await client.ingest(
            "user_demo_001",
            {
                "event_type": "click",
                "item_token": "item_42",
                "item_category": "product",
                "engagement_depth": 0.8,
            },
        )
        print(f"Ingest: {ingest_resp}")

        # Run simulation
        sim_resp = await client.simulate(
            "user_demo_001",
            {
                "time_bucket": "evening",
                "device_class": "mobile",
                "entry_point": "social",
                "session_depth": 1,
            },
        )
        print(f"Simulation basis: {sim_resp.simulation_basis}")

        # Get recommendations
        rec_resp = await client.recommend(
            "user_demo_001",
            {
                "time_bucket": "evening",
                "device_class": "mobile",
                "entry_point": "social",
            },
            n=6,
        )
        print(f"Recommendations received: {len(rec_resp.recommendations)}")
        for rec in rec_resp.recommendations:
            print(f"  - {rec.item_name} ({rec.recommendation_type}): {rec.confidence}")

    except Exception as e:
        print(f"Error: {e}")


async def example_orchestrator_usage():
    """Example of using the ARCHE Orchestrator for full pipeline."""
    pipeline = ArchePipeline("http://127.0.0.1:8000")

    try:
        state = await pipeline.execute_full_flow(
            user_token="user_pipeline_001",
            signal={
                "event_type": "view",
                "item_category": "electronics",
                "engagement_depth": 0.6,
            },
            context={
                "time_bucket": "afternoon",
                "device_class": "desktop",
                "entry_point": "search",
            },
        )

        print(f"Pipeline execution complete")
        print(f"Ingest status: {state.ingest_response}")
        print(f"Simulation basis: {state.simulation_response.get('simulation_basis') if state.simulation_response else 'N/A'}")
        print(f"Recommendations: {len(state.recommendation_response.get('recommendations', [])) if state.recommendation_response else 0}")
        if state.errors:
            print(f"Errors: {state.errors}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("=== ARCHE SDK Example ===")
    asyncio.run(example_sdk_usage())

    print("\n=== ARCHE Orchestrator Example ===")
    asyncio.run(example_orchestrator_usage())
