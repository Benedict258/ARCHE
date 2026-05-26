#!/usr/bin/env python
"""Quick test of review generation fixes."""
import sys
sys.path.insert(0, '.')

from agents.review_generation_agent import ReviewGenerationAgent
from agents.simulation_builder import build_cold_start_simulation

# Test data
history = [
    {'item_name': 'Cactus Restaurant', 'item_category': 'fine_dining', 'rating': 4, 'review_text': 'An excellent dining experience. The service was impeccable and the food beautifully presented.'},
    {'item_name': 'Sony WH-1000XM5', 'item_category': 'electronics', 'rating': 5, 'review_text': 'Outstanding audio quality. The noise cancellation technology is industry-leading.'},
    {'item_name': 'Atomic Habits', 'item_category': 'books', 'rating': 4, 'review_text': 'A practical and well-researched guide to behaviour change. Highly recommended.'}
]

print("=" * 70)
print("TEST 1: Formal English Review (Check for 'Atomic Habits' text leaking)")
print("=" * 70)

item = {'name': 'Half of a Yellow Sun', 'category': 'african_literature', 'price_tier': 'mid', 'attributes': {'author': 'Chimamanda Ngozi Adichie', 'genre': 'literary fiction'}}
context = {'time_of_day': 'afternoon', 'region': 'Lagos Island'}

result = ReviewGenerationAgent._generated_review_text(
    history=history, 
    item=item, 
    predicted_rating=4, 
    register='formal_english', 
    context=context
)

print("\n✓ Generated Review:")
print(result)

# Check for the bug
if "A practical and well-researched" in result:
    print("\n❌ FAILED: Historical text leaked into review!")
else:
    print("\n✅ PASSED: No historical text leaked")

print("\n" + "=" * 70)
print("TEST 2: Context Extraction (Check for 'afternoon' and 'Lagos Island')")
print("=" * 70)

if "afternoon" in result.lower():
    print("✅ PASSED: 'afternoon' context properly included")
else:
    print("❌ FAILED: 'afternoon' context missing")

if "Lagos Island".lower() in result.lower():
    print("✅ PASSED: 'Lagos Island' region properly included")
else:
    print("❌ FAILED: 'Lagos Island' region missing")

print("\n" + "=" * 70)
print("TEST 3: Mixed Pidgin Review (with history leaking check)")
print("=" * 70)

pidgin_history = [
    {'item_name': 'Mr Biggs', 'item_category': 'fast_food', 'rating': 2, 'review_text': 'Abeg make dem upgrade this place. E be like say dem no care again.'}
]

pidgin_item = {'name': 'The Place Restaurant Lekki', 'category': 'nigerian_cuisine', 'price_tier': 'mid', 'attributes': {'cuisine': 'Nigerian', 'setting': 'casual dining'}}
pidgin_context = {'time_of_day': 'evening', 'region': 'Lagos Mainland'}

pidgin_result = ReviewGenerationAgent._generated_review_text(
    history=pidgin_history,
    item=pidgin_item,
    predicted_rating=4,
    register='mixed_pidgin',
    context=pidgin_context
)

print("\n✓ Generated Review:")
print(pidgin_result)

if "Abeg make dem upgrade" in pidgin_result:
    print("\n❌ FAILED: Mr Biggs review text leaked!")
else:
    print("\n✅ PASSED: No historical text from Mr Biggs leaked")

print("\nAll tests completed!")
