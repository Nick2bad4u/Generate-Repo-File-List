"""Video assembly via PIL slides + TTS narration + ffmpeg.

Replaces the original `training-video-generator` integration assumption
(see docs/bea-training-engine-tooling-findings.md). The fork was a doc-prep
tool, not a deck-to-MP4 renderer, so we DIY here.

Pipeline:
1. For each slide in deck.json, render a PNG via PIL using the brand theme
2. For each slide, synthesize narration audio via TTSClient
3. Use ffmpeg to concatenate slide PNGs (timed to narration duration) with
   the concatenated audio track into one MP4

Output: single MP4 ready to play.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from tts_client import TTSClient


@dataclass
class VideoRenderer:
    brand: dict[str, Any]
    tts: TTSClient | None = None

    def __post_init__(self) -> None:
        self.tts = self.tts or TTSClient()

    def render(self, deck: dict[str, Any], output_path: Path) -> None:
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "ffmpeg not found. Install with: brew install ffmpeg (macOS) "
                "or apt install ffmpeg (Linux)"
            )

        slides = deck.get("slides", [])
        if not slides:
            raise ValueError("deck.json has no slides")

        deck_language = deck.get("language") or self.brand.get("default_language", "en-US")
        voice = self.tts.resolve_voice(self.brand, deck_language)

        # timing.json sidecar — captions_generator.py reads this for accurate SRT.
        timing: list[dict[str, float]] = []

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            slide_paths: list[Path] = []
            audio_paths: list[Path] = []
            durations: list[float] = []

            cursor = 0.0
            for i, slide in enumerate(slides, start=1):
                # 1. Render slide image
                img_path = tmp_dir / f"slide_{i:02d}.png"
                self._render_slide(slide, img_path)
                slide_paths.append(img_path)

                # 2. Synthesize narration audio
                audio_path = tmp_dir / f"slide_{i:02d}.wav"
                narration = (
                    slide.get("narration")
                    or slide.get("speaker_intent")
                    or slide.get("title", "")
                )
                self.tts.synthesize(narration, audio_path, voice=voice)
                audio_paths.append(audio_path)

                # 3. Measure audio duration so the slide displays for that long
                dur = _audio_duration(audio_path)
                durations.append(dur)
                timing.append(
                    {
                        "index": i,
                        "start_seconds": round(cursor, 3),
                        "end_seconds": round(cursor + dur, 3),
                        "duration_seconds": round(dur, 3),
                    }
                )
                cursor += dur

            # 4. Build a concat list for ffmpeg's image2 demuxer
            slides_concat = tmp_dir / "slides.txt"
            slides_concat.write_text(_build_image_concat(slide_paths, durations))

            audio_concat = tmp_dir / "audio.txt"
            audio_concat.write_text(_build_audio_concat(audio_paths))

            # 5. Concatenate audio first
            full_audio = tmp_dir / "narration.wav"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(audio_concat), "-c", "copy", str(full_audio),
                ],
                check=True, capture_output=True,
            )

            # 6. Encode video from slides + audio
            output_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0", "-i", str(slides_concat),
                    "-i", str(full_audio),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest",
                    "-r", str(self.brand.get("video", {}).get("fps", 30)),
                    str(output_path),
                ],
                check=True, capture_output=True,
            )

            # 7. Sidecar timing.json next to the MP4 for captions_generator
            timing_path = output_path.with_suffix(".timing.json")
            timing_path.write_text(json.dumps({"slides": timing}, indent=2))

    # ---- slide rendering ----

    def _render_slide(self, slide: dict[str, Any], path: Path) -> None:
        res = self.brand.get("video", {}).get("resolution", "1920x1080")
        width, height = (int(x) for x in res.split("x"))
        bg = self.brand.get("background_color", "#FFFFFF")
        primary = self.brand.get("primary_color", "#000000")
        accent = self.brand.get("accent_color", primary)

        img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(img)

        # Best-effort font load — falls back to default if the brand font isn't installed
        title_font = _load_font(self.brand.get("font_heading", "DejaVuSans-Bold"), 80)
        body_font = _load_font(self.brand.get("font_body", "DejaVuSans"), 40)

        # Title
        title = slide.get("title", "")
        draw.text((width * 0.08, height * 0.18), title, font=title_font, fill=primary)

        # Bullets
        y = height * 0.36
        for bullet in slide.get("bullets", []):
            draw.text((width * 0.10, y), f"• {bullet}", font=body_font, fill=primary)
            y += 70

        # Slide index badge
        idx = slide.get("index", "")
        draw.text(
            (width * 0.92, height * 0.92), str(idx),
            font=body_font, fill=accent, anchor="rs",
        )

        # Logo if it exists
        logo_path = Path(self.brand.get("logo_path", ""))
        if logo_path.exists():
            try:
                logo = Image.open(logo_path).convert("RGBA")
                # Scale to ~10% of slide width
                target_w = int(width * 0.10)
                ratio = target_w / logo.width
                logo = logo.resize((target_w, int(logo.height * ratio)))
                img.paste(logo, (int(width * 0.04), int(height * 0.04)), logo)
            except Exception:
                pass  # Don't crash on a logo issue

        img.save(path)


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Try to load a font by name; fall back to the PIL default."""
    candidates = [
        name,
        f"{name}.ttf",
        f"/usr/share/fonts/truetype/dejavu/{name}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _build_image_concat(paths: list[Path], durations: list[float]) -> str:
    """Build the ffmpeg image2 concat demuxer list."""
    lines: list[str] = []
    for path, dur in zip(paths, durations, strict=False):
        lines.append(f"file '{path.as_posix()}'")
        lines.append(f"duration {dur:.3f}")
    # Repeat the last frame so concat doesn't drop it
    lines.append(f"file '{paths[-1].as_posix()}'")
    return "\n".join(lines) + "\n"


def _build_audio_concat(paths: list[Path]) -> str:
    return "\n".join(f"file '{p.as_posix()}'" for p in paths) + "\n"


def _audio_duration(path: Path) -> float:
    """Use ffprobe to read audio duration in seconds."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python video_renderer.py <deck.json> <brand/theme.json> <out.mp4>")
        sys.exit(1)
    deck = json.loads(Path(sys.argv[1]).read_text())
    brand = json.loads(Path(sys.argv[2]).read_text())
    VideoRenderer(brand=brand).render(deck, Path(sys.argv[3]))
