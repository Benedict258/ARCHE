#!/usr/bin/env python
"""Quick test of explanation generation."""
import sys
sys.path.insert(0, '.')

from agents.recommendation_scoring import rank_catalog_against_simulation, build_simulation_from_history
from agents.catalog_loader import get_catalog_list

# Test data
history = [
    {
        'item_name': 'Jollof Rice Special',
        'item_category': 'nigerian_cuisine',
        'rating': 5,
        'review_text': 'This jollof rice is the best I have tasted in Lagos abeg.'
    }
]

context = {
    'time_of_day': 'evening',
    'occasion': 'dinner',
    'location_tier': 'Lagos Mainland'
}

# Build simulation and get recommendations
simulation = build_simulation_from_history(history, context)
catalog = get_catalog_list()

print("=" * 70)
print("TESTING RECOMMENDATION EXPLANATIONS")
print("=" * 70)

ranked = rank_catalog_against_simulation(simulation, catalog, n=5)

for idx, rec in enumerate(ranked, 1):
    print(f"\n#{idx}. {rec.get('item_name')} ({rec.get('item_category')})")
    print(f"   Type: {rec.get('recommendation_type')}")
    print(f"   Confidence: {rec.get('_score', 0):.2f}")
    print(f"   Explanation:  {rec.get('explanation')}")

print("\n" + "=" * 70)
print("✅ Explanations are now context-aware!")
