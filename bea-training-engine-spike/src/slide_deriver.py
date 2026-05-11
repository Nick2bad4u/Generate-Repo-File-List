"""Claude-based slide derivation.

Takes the audio overview transcript (if available) plus the source corpus and
produces a structured deck (slides + per-slide narration) that the renderer
consumes.

Why Claude here, not NotebookLM:
- The NotebookLM Enterprise API exposes audio overviews; structured slide
  decks aren't a documented output type.
- Even when the transcript is available, we need to slice it into discrete
  slides with titles, bullets, and timing — that's exactly what an LLM does
  well from a long-form input.
- Putting the slide derivation in Claude (vs prompting the audio transcription
  to be slide-shaped) keeps NotebookLM in its strongest mode (RAG + audio)
  and Claude in its strongest mode (structured output from prose).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic


@dataclass
class ClaudeSlideDeriver:
    """Derives a slide deck from a topic + transcript + source corpus."""

    model: str = ""
    api_key: str = ""

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = self.model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY missing; set in .env")

    def derive(
        self,
        topic: str,
        slide_count: int,
        target_seconds: int,
        transcript: str,
        source_texts: list[dict],
        slide_outline_prompt: str,
        narration_prompt: str,
    ) -> dict[str, Any]:
        """Single Claude call that produces both outline + narration in one shot.

        Splitting outline + narration into two calls is a Phase 1 refinement;
        for the spike, one structured call is enough and saves time + tokens.
        """
        client = Anthropic(api_key=self.api_key)

        sources_block = "\n\n---\n\n".join(
            f"## SOURCE: {s['name']}\n\n{s['text']}" for s in source_texts
        )
        transcript_block = transcript or "(no transcript available)"

        system = (
            f"{slide_outline_prompt}\n\n---\n\n{narration_prompt}\n\n"
            "Return one JSON object combining both: a `slides` array per the "
            "outline format, with a `narration` field on each slide containing "
            "the spoken text per the narration format. No prose outside the JSON."
        )

        user = (
            f"## TOPIC\n{topic}\n\n"
            f"## CONSTRAINTS\n- {slide_count} slides total\n"
            f"- ~{target_seconds} seconds total\n"
            f"- ~{target_seconds / slide_count:.1f} seconds per slide\n\n"
            f"## NOTEBOOKLM AUDIO OVERVIEW TRANSCRIPT\n\n{transcript_block}\n\n"
            f"## BEA SOURCE CORPUS\n\n{sources_block}\n\n"
            f"## OUTPUT\nReturn the deck JSON now."
        )

        response = client.messages.create(
            model=self.model,
            max_tokens=8000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        text = response.content[0].text
        return _extract_json(text)


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of Claude's response.

    Claude usually returns clean JSON when asked, but if it wraps it in
    backticks or prose, this strips those.
    """
    text = text.strip()
    # Strip code fences
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    # Find first { ... last }
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"No JSON object found in Claude response: {text[:200]}...")
    return json.loads(text[start : end + 1])
