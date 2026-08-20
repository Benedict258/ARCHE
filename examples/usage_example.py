"""Example usage of the ARCHE SDK client against a running API instance."""

import asyncio
from sdk.client import ArcheClient


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


if __name__ == "__main__":
    print("=== ARCHE SDK Example ===")
    asyncio.run(example_sdk_usage())
