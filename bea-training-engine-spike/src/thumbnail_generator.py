"""Thumbnail generator with two backends.

The BEA `YouTube-Thumbnail` repo (https://github.com/BEA-BOLD-EVOLUTION/YouTube-Thumbnail)
is a Next.js + tRPC web service, not a library. The engine has two ways to
produce thumbnails:

1. `PILThumbnailGenerator` (default) — local PIL render. Branded but plain.
   Works today, no external service required, deterministic. Good for spike +
   Phase 1 when consistency matters more than visual polish.

2. `TRPCThumbnailGenerator` — calls the YouTube-Thumbnail web service via its
   tRPC HTTP API. Produces AI-generated thumbnails (Gemini). Requires the
   service to be running and reachable; output style varies per call.

Choose via THUMBNAIL_ENGINE env var ("pil" default, "trpc" opt-in). Both emit
a 1280×720 PNG suitable for YouTube's thumbnails.set endpoint.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont


YOUTUBE_THUMB_WIDTH = 1280
YOUTUBE_THUMB_HEIGHT = 720


@dataclass
class PILThumbnailGenerator:
    """Local PIL render. Brand-consistent, deterministic, fast."""

    brand: dict[str, Any]

    def generate(
        self,
        title: str,
        output_path: Path,
        subtitle: str | None = None,
    ) -> Path:
        """Render a branded thumbnail at output_path."""
        bg = self.brand.get("background_color", "#000000")
        primary = self.brand.get("primary_color", "#FFFFFF")
        accent = self.brand.get("accent_color", primary)
        brand_name = self.brand.get("brand_name", "Bold Evolution Agency")

        img = Image.new("RGB", (YOUTUBE_THUMB_WIDTH, YOUTUBE_THUMB_HEIGHT), bg)
        draw = ImageDraw.Draw(img)

        # Accent stripe down the left edge
        draw.rectangle((0, 0, 14, YOUTUBE_THUMB_HEIGHT), fill=accent)

        # Title — wrap to fit
        title_font = _load_font(self.brand.get("font_heading", "DejaVuSans-Bold"), 88)
        body_font = _load_font(self.brand.get("font_body", "DejaVuSans"), 36)
        brand_font = _load_font(self.brand.get("font_body", "DejaVuSans"), 28)

        wrapped = _wrap(title, title_font, YOUTUBE_THUMB_WIDTH - 200)
        # Vertically center the title block
        line_height = title_font.size + 16
        total_height = len(wrapped) * line_height
        y = (YOUTUBE_THUMB_HEIGHT - total_height) // 2 - 30
        for line in wrapped:
            draw.text((80, y), line, font=title_font, fill=primary)
            y += line_height

        # Subtitle (e.g. module ID, topic tag) directly under title
        if subtitle:
            draw.text((80, y + 8), subtitle, font=body_font, fill=accent)

        # Brand name bottom-right
        draw.text(
            (YOUTUBE_THUMB_WIDTH - 40, YOUTUBE_THUMB_HEIGHT - 40),
            brand_name,
            font=brand_font, fill=primary, anchor="rs",
        )

        # Logo bottom-left if available
        logo_path = Path(self.brand.get("logo_path", ""))
        if logo_path.exists():
            try:
                logo = Image.open(logo_path).convert("RGBA")
                target_h = 90
                ratio = target_h / logo.height
                logo = logo.resize((int(logo.width * ratio), target_h))
                img.paste(logo, (40, YOUTUBE_THUMB_HEIGHT - target_h - 40), logo)
            except Exception:
                pass

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        return output_path


@dataclass
class TRPCThumbnailGenerator:
    """Calls the BEA YouTube-Thumbnail service via its tRPC HTTP API.

    Supports two of the service's four modes:

    - text_prompt: pre-upload generation from title + subtitle. Fast but the
      tool can't "see" the video content (it doesn't exist on YouTube yet).
    - video_url: post-upload generation by passing the YouTube URL to the
      tool, which downloads + analyzes the video via Gemini Vision. Higher
      quality but requires the video to be on YouTube already.

    Pattern (set via THUMBNAIL_TIMING env var):
    - "pre": generate from text, upload with thumbnail in one shot
    - "post": upload without thumbnail, get URL, call tool, apply thumbnail

    Status of wire shape: STUB. Fill in the actual tRPC procedure name and
    request body shape after inspecting apps/api/src/trpc/routers/*.ts in the
    YouTube-Thumbnail repo. The guesses below are based on tRPC v11
    conventions and the README's described modes.
    """

    base_url: str = ""
    api_key: str | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url or os.environ.get(
            "YOUTUBE_THUMBNAIL_SERVICE_URL", "http://localhost:4000"
        )
        self.api_key = self.api_key or os.environ.get("YOUTUBE_THUMBNAIL_API_KEY")

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _call_and_download(self, body: dict, output_path: Path) -> Path:
        """POST to tRPC, parse imageUrl, download to output_path."""
        # TODO: confirm endpoint path + procedure name + body envelope.
        response = requests.post(
            f"{self.base_url}/trpc/thumbnail.generate",
            headers=self._headers(),
            json=body,
            timeout=180,
        )
        response.raise_for_status()
        result = response.json()

        # tRPC v11 returns { result: { data: { ... } } }
        image_url = (
            result.get("result", {}).get("data", {}).get("imageUrl")
        )
        if not image_url:
            raise RuntimeError(
                f"YouTube-Thumbnail service didn't return imageUrl. "
                f"Got: {json.dumps(result)[:300]}"
            )

        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img_response.content)

        # Normalize to 1280×720 for YouTube
        img = Image.open(output_path)
        if img.size != (YOUTUBE_THUMB_WIDTH, YOUTUBE_THUMB_HEIGHT):
            img = img.resize((YOUTUBE_THUMB_WIDTH, YOUTUBE_THUMB_HEIGHT), Image.LANCZOS)
            img.save(output_path, "PNG")
        return output_path

    def generate(
        self,
        title: str,
        output_path: Path,
        subtitle: str | None = None,
        style: str = "Cinematic",
    ) -> Path:
        """Pre-upload: generate from text prompt (no video exists yet)."""
        prompt = f"BEA training thumbnail. Title: {title}."
        if subtitle:
            prompt += f" Subtitle: {subtitle}."
        prompt += " Style: clean, professional, brand-consistent. No text overlays."

        body = {
            "input": {
                "mode": "text_prompt",
                "prompt": prompt,
                "style": style,
                "aspectRatio": "16:9",
            }
        }
        return self._call_and_download(body, output_path)

    def generate_from_url(
        self,
        youtube_url: str,
        output_path: Path,
        style: str = "Cinematic",
    ) -> Path:
        """Post-upload: pass the published YouTube URL to the tool.

        The tool downloads the video, analyzes it via Gemini Vision, and
        produces a thumbnail informed by the actual content.
        """
        body = {
            "input": {
                "mode": "video_url",
                "videoUrl": youtube_url,
                "style": style,
                "aspectRatio": "16:9",
            }
        }
        return self._call_and_download(body, output_path)


def make_generator(brand: dict[str, Any]):
    """Pick the right generator based on THUMBNAIL_ENGINE env var."""
    engine = os.environ.get("THUMBNAIL_ENGINE", "pil")
    if engine == "trpc":
        return TRPCThumbnailGenerator()
    if engine == "pil":
        return PILThumbnailGenerator(brand=brand)
    raise ValueError(f"Unknown THUMBNAIL_ENGINE: {engine}")


# ---- small helpers ----


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
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


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text into lines that fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if font.getlength(candidate) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    # Cap at 3 lines to keep the thumbnail readable
    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] = lines[-1].rstrip() + "…"
    return lines


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python thumbnail_generator.py <brand.json> <output.png> <title> [subtitle]")
        sys.exit(1)
    brand_data = json.loads(Path(sys.argv[1]).read_text())
    title_arg = sys.argv[3]
    subtitle_arg = sys.argv[4] if len(sys.argv) > 4 else None
    gen = make_generator(brand_data)
    gen.generate(title_arg, Path(sys.argv[2]), subtitle_arg)
    print(f"Wrote {sys.argv[2]}")
