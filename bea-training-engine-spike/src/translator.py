"""Cloud Translation API wrapper.

Translates a deck.json from English to a target language (default: es-US for
Latin American Spanish, the largest Spanish-speaking TikTok creator market).

What gets translated:
- slide.title          (visible on the rendered slide)
- slide.bullets[]      (visible on the rendered slide)
- slide.narration      (spoken by TTS)

What does NOT get translated:
- "TikTok", "LIVE", BEA, "Lion", "Universe", and other platform / product
  proper nouns (handled via a glossary so they pass through verbatim)
- Slide index, sources_cited, source_version, and other metadata

Output: a sibling deck file with deck.language set + translated text.
"""

from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google.cloud import translate_v3


# Terms that must pass through translation untouched. TikTok product names
# in particular get mangled badly by general-purpose MT (e.g., "Lion" → "León").
DO_NOT_TRANSLATE = [
    "TikTok",
    "TikTok LIVE",
    "LIVE Studio",
    "FYP",
    "Bold Evolution Agency",
    "BEA",
    "Toklytics",
    "Toklytics-LiveIQ",
    "Lion",
    "Universe",
    "Galaxy",
    "Rocket",
    "Star",
    "Diamond",
    "Coin",
    "Gift",
    "Battle",
    "Gifter",
]


@dataclass
class DeckTranslator:
    """Translates a deck.json's user-visible text. Preserves structure."""

    project_id: str = ""
    location: str = "global"
    do_not_translate: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.project_id = self.project_id or os.environ.get("GCP_PROJECT_ID", "")
        if not self.project_id:
            raise RuntimeError(
                "GCP_PROJECT_ID not set. Cloud Translation needs the project ID "
                "(not just the project number). See .env.example."
            )
        if not self.do_not_translate:
            self.do_not_translate = tuple(DO_NOT_TRANSLATE)

    def translate_deck(
        self,
        deck: dict[str, Any],
        target_language: str = "es-US",
        source_language: str = "en-US",
    ) -> dict[str, Any]:
        """Return a new deck with all user-visible text translated."""
        client = translate_v3.TranslationServiceClient()
        parent = f"projects/{self.project_id}/locations/{self.location}"

        # Gather every string we need translated in one batch call (cheaper +
        # gives the model more context). Keep a parallel list of (slot_path)
        # so we can write results back into the right place.
        strings: list[str] = []
        slots: list[tuple[int, str, int | None]] = []  # (slide_idx, field, bullet_idx_or_None)

        for i, slide in enumerate(deck.get("slides", [])):
            if slide.get("title"):
                strings.append(slide["title"])
                slots.append((i, "title", None))
            for b_idx, bullet in enumerate(slide.get("bullets", [])):
                if bullet:
                    strings.append(bullet)
                    slots.append((i, "bullets", b_idx))
            if slide.get("narration"):
                strings.append(slide["narration"])
                slots.append((i, "narration", None))

        if not strings:
            return copy.deepcopy(deck)

        # Cloud Translation expects ISO codes ("es", "en") not locale-tagged
        # ("es-US", "en-US"). Use just the language portion.
        src = source_language.split("-")[0]
        tgt = target_language.split("-")[0]

        protected = _wrap_protected_terms(strings, self.do_not_translate)

        response = client.translate_text(
            parent=parent,
            contents=protected,
            source_language_code=src,
            target_language_code=tgt,
            mime_type="text/html",  # so the <span translate="no"> tags are honored
        )

        translated = [_unwrap_protected_terms(t.translated_text) for t in response.translations]

        # Write translations back into a deep-copied deck.
        out = copy.deepcopy(deck)
        out["language"] = target_language
        out.setdefault("source_language", source_language)

        for (slide_idx, field, bullet_idx), text in zip(slots, translated, strict=True):
            slide = out["slides"][slide_idx]
            if field == "bullets":
                slide["bullets"][bullet_idx] = text
            else:
                slide[field] = text

        return out


def _wrap_protected_terms(strings: list[str], terms: tuple[str, ...]) -> list[str]:
    """Wrap do-not-translate terms in <span translate="no">..</span>."""
    # Order longest-first so "TikTok LIVE" matches before "TikTok"
    sorted_terms = sorted(terms, key=len, reverse=True)
    out = []
    for s in strings:
        for term in sorted_terms:
            s = s.replace(term, f'<span translate="no">{term}</span>')
        out.append(s)
    return out


def _unwrap_protected_terms(text: str) -> str:
    """Remove the <span translate="no"> wrappers from translated output."""
    return text.replace('<span translate="no">', "").replace("</span>", "")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python translator.py <deck.json> <out-deck.json> [target=es-US]")
        sys.exit(1)
    target = sys.argv[3] if len(sys.argv) > 3 else "es-US"
    deck = json.loads(Path(sys.argv[1]).read_text())
    translated = DeckTranslator().translate_deck(deck, target_language=target)
    Path(sys.argv[2]).write_text(json.dumps(translated, indent=2, ensure_ascii=False))
    print(f"Wrote {sys.argv[2]} (language={target})")
