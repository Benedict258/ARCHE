from __future__ import annotations

import json
import re
from typing import Any

from agents.simulation_agent import SimulationAgent

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.DOTALL)


def _strip_wrappers(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = _CODE_FENCE_RE.sub("", cleaned).strip()
    return cleaned


def _best_effort_json(text: str) -> dict[str, Any] | None:
    cleaned = _strip_wrappers(text)
    if not cleaned:
        return None

    candidates = [cleaned]
    if "'" in cleaned and '"' not in cleaned:
        candidates.append(cleaned.replace("'", '"'))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


async def repair_payload_from_text(
    raw_input: str,
    *,
    schema_name: str,
    schema_description: str,
    example_payload: dict[str, Any],
) -> dict[str, Any]:
    """Convert pasted free text or malformed JSON into a structured payload.

    The function first tries to parse JSON directly. If that fails and an LLM
    provider is configured, it asks the LLM to normalize the text into the
    expected JSON object.
    """
    raw_text = (raw_input or "").strip()
    if not raw_text:
        return {}

    direct = _best_effort_json(raw_text)
    if direct is not None:
        return direct

    sim_agent = SimulationAgent()
    if sim_agent.llm is not None:
        system_prompt = (
            f"You convert user input into a valid JSON object for {schema_name}. "
            f"Return only JSON. {schema_description}"
        )
        user_prompt = (
            f"Expected schema example:\n{json.dumps(example_payload, indent=2, ensure_ascii=False)}\n\n"
            f"Raw user input to normalize:\n{raw_text}\n\n"
            "Return a single JSON object that matches the schema."
        )
        try:
            content = await sim_agent.call_llm(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.0)
            repaired = _best_effort_json(content)
            if repaired is not None:
                return repaired
        except Exception:
            pass

    return {"raw_input": raw_text}
