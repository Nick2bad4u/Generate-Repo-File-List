"""Thin wrapper around `training-video-generator` (forked).

Same pattern as `notebooklm_client.py` — the orchestrator depends only on this
file's `VideoRenderer` class; this file is the only place the upstream fork's
API surfaces. Fill in TODOs Day 2 after reading
`forks/training-video-generator/README.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

# TODO Day 2: replace with the actual import path.
# The fork likely exposes either a CLI or a Python function. If CLI-only,
# this wrapper shells out via subprocess. If Python, import directly.


@dataclass
class VideoRenderer:
    """Wrapper that takes a deck JSON + brand config and produces an MP4."""

    brand: dict[str, Any]

    def render(self, deck: dict[str, Any], output_path: Path) -> None:
        """Render the deck to MP4 at output_path.

        Expected deck shape (matches notebooklm_client.generate_deck output):
            {
              "topic": "...",
              "target_seconds": 90,
              "slides": [
                {"index": 1, "title": "...", "bullets": [...], "narration": "..."},
                ...
              ]
            }

        Expected brand shape (see brand/theme.json):
            {
              "logo_path": "...",
              "primary_color": "#...",
              "secondary_color": "#...",
              "font_heading": "...",
              "font_body": "...",
              "intro_seconds": 2,
              "outro_seconds": 2,
              "voice": "..."
            }

        TODO Day 2: implement. Two likely paths:

        Path A — training-video-generator exposes a Python function:
            from training_video_generator import render
            render(slides=deck["slides"], theme=self.brand, out=output_path)

        Path B — CLI only:
            import subprocess
            subprocess.run(
                ["training-video-generator", "--deck", deck_json_path,
                 "--theme", brand_json_path, "--out", output_path],
                check=True,
            )

        Choose based on the fork's README. If Path B, write `deck` and
        `self.brand` to temp JSON files first.
        """
        raise NotImplementedError("TODO Day 2: implement via training-video-generator")
