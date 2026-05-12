"""SRT captions generator.

Takes the deck (slide-by-slide narration text) and the timing sidecar
written by video_renderer.py, produces a clean SRT file.

Each slide becomes one or more SRT cues. Long narration is split by
sentence to keep on-screen text readable (~42 chars per line, ~2 lines
max per cue).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAX_CHARS_PER_LINE = 42
MAX_LINES_PER_CUE = 2
MIN_CUE_SECONDS = 1.0  # don't flash captions faster than this


def generate_srt(deck_path: Path, timing_path: Path, output_path: Path) -> Path:
    """Produce an SRT file at output_path. Returns the path."""
    deck = json.loads(deck_path.read_text())
    timing = json.loads(timing_path.read_text())["slides"]

    slides = deck.get("slides", [])
    if len(slides) != len(timing):
        raise ValueError(
            f"deck has {len(slides)} slides but timing has {len(timing)}"
        )

    cues: list[dict[str, Any]] = []
    for slide, t in zip(slides, timing, strict=True):
        narration = slide.get("narration", "")
        start = t["start_seconds"]
        end = t["end_seconds"]
        slide_dur = end - start

        sentences = _split_sentences(narration)
        if not sentences:
            continue

        # Distribute slide duration across sentences proportional to char count
        total_chars = sum(len(s) for s in sentences) or 1
        cursor = start
        for sent in sentences:
            share = (len(sent) / total_chars) * slide_dur
            share = max(share, MIN_CUE_SECONDS)
            cue_end = min(cursor + share, end)
            cues.append(
                {
                    "start": cursor,
                    "end": cue_end,
                    "text": _wrap_text(sent),
                }
            )
            cursor = cue_end

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_format_srt(cues))
    return output_path


def _split_sentences(text: str) -> list[str]:
    """Naive sentence splitter — works well for narration prose."""
    text = text.strip()
    if not text:
        return []
    # Split on sentence-ending punctuation but keep the punctuation
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _wrap_text(sentence: str) -> str:
    """Soft-wrap a sentence to max 2 lines of ~42 chars."""
    words = sentence.split()
    if not words:
        return sentence

    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= MAX_CHARS_PER_LINE:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    # Cap at 2 lines; truncate excess with ellipsis (rare in well-written narration)
    if len(lines) > MAX_LINES_PER_CUE:
        lines = lines[:MAX_LINES_PER_CUE]
        lines[-1] = lines[-1].rstrip() + "…"

    return "\n".join(lines)


def _format_srt(cues: list[dict[str, Any]]) -> str:
    """Render cues as SRT text."""
    out: list[str] = []
    for i, cue in enumerate(cues, start=1):
        out.append(str(i))
        out.append(f"{_ts(cue['start'])} --> {_ts(cue['end'])}")
        out.append(cue["text"])
        out.append("")
    return "\n".join(out) + "\n"


def _ts(seconds: float) -> str:
    """Seconds → 'HH:MM:SS,mmm' SRT timestamp."""
    millis = int(round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python captions_generator.py <deck.json> <timing.json> <out.srt>")
        sys.exit(1)
    generate_srt(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(f"Wrote {sys.argv[3]}")
