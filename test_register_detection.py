pidgin_markers = ("sha", "abi", "sef", "abeg", "na im", "e be like", "naija", "9ja", "oga", "no cap", "fr", "omo", "nah", "mad", "clean", "slaps", "vibe", "it is giving", "unhinged", "chief", "guy", "joor", "ahn", "shey")
nig_eng_markers = ("very okay", "too much", "value", "price", "worth it", "not bad", "food", "service", "practical", "quality", "experience", "decent")
formal_markers = ("overall", "however", "recommend", "consistent", "research", "thoroughly", "professional")

review_text = "Omo this footwear is too clean, fr! The comfort is out of this world. No cap, best purchase this year."
combined = review_text.lower()

pidgin_score = sum(1 for marker in pidgin_markers if marker in combined)
nig_eng_score = sum(1 for marker in nig_eng_markers if marker in combined)
formal_score = sum(1 for marker in formal_markers if marker in combined)

print(f"Pidgin score: {pidgin_score}")
print(f"Nigerian English score: {nig_eng_score}")
print(f"Formal score: {formal_score}")

if pidgin_score >= 2:
    register = "casual_pidgin" if pidgin_score >= 4 else "mixed_pidgin"
elif nig_eng_score >= 2 and formal_score < 2:
    register = "nigerian_english"
else:
    register = "formal_english"

print(f"Detected register: {register}")
