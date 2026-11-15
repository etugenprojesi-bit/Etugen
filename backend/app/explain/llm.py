"""Optional plain-language explanations of rotation cards with Claude.

The app works fully without this: when no API credentials are configured, or
the call fails or is declined, the UI builds template explanations from the
same structured card fields. The model only rephrases facts we send; it gets
no coordinates, and the prompt forbids adding numbers or claims.
"""

from __future__ import annotations

import json
import os

import anthropic

DEFAULT_MODEL = "claude-opus-5-5"
SYSTEM = (
    "You explain crop-rotation comparison results to farmers who are not technical. "
    "Use only the facts in the JSON you receive: do not add numbers, crops, prices, yields or "
    "advice that are not in it. Say plainly when something is uncertain or a proxy. "
    "For each card write 2-3 short sentences: what the rotation is, its main strengths, and its "
    "main risk or data gap. End every card by reminding that a local expert should check it. "
    "Write in {language}."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "text": {"type": "string"}},
                "required": ["id", "text"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["cards"],
    "additionalProperties": False,
}


def card_facts(card: dict, lang: str) -> dict:
    name_key = "tr" if lang == "tr" else "en"
    return {
        "id": card["id"],
        "kind": card["kind"],
        "years": [[s["name"][name_key] for s in y] or ["(no modelled crop)"] for y in card["years"]],
        "total_score": card["total"],
        "subscores": {k: v["value"] for k, v in card["subscores"].items()},
        "irrigation_need_mm_per_year": card["irrigation_need_mm_per_year"],
        "benefits": [b["text"] for b in card["benefits"]],
        "risks": [r["text"].format(**r["params"]) if "{" in r["text"] else r["text"] for r in card["risks"]],
        "data_gaps": [d["text"] for d in card["data_gaps"]],
        "confidence": card["confidence"]["level"],
    }


def _configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


async def explain_cards(cards: list[dict], lang: str) -> dict:
    if not _configured():
        return {"mode": "template", "reason": "no_api_key"}
    model = os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL
    facts = [card_facts(c, lang) for c in cards]
    client = anthropic.AsyncAnthropic(timeout=60.0, max_retries=1)
    try:
        response = await client.beta.messages.create(
            model=model,
            max_tokens=16000,
            system=SYSTEM.format(language="Turkish" if lang == "tr" else "English"),
            messages=[{"role": "user", "content": json.dumps({"cards": facts}, ensure_ascii=False)}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            # Server-side fallback if a safety classifier declines (Claude API only).
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.APIConnectionError:
        return {"mode": "template", "reason": "llm_unreachable"}
    except anthropic.RateLimitError:
        return {"mode": "template", "reason": "llm_rate_limited"}
    except anthropic.APIStatusError as e:
        return {"mode": "template", "reason": f"llm_error_{e.status_code}"}
    if response.stop_reason == "refusal":
        return {"mode": "template", "reason": "llm_refused"}
    text = next((b.text for b in response.content if b.type == "text"), None)
    try:
        texts = {c["id"]: c["text"] for c in json.loads(text or "")["cards"]}
    except (ValueError, KeyError, TypeError):
        return {"mode": "template", "reason": "llm_bad_output"}
    return {"mode": "llm", "model": response.model, "texts": texts,
            "note": "AI-generated wording of the facts on each card; numbers come from the model above."}
