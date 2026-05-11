# BEA Brand Assets — Spike Configuration

Before Day 2 video render, populate this directory with the real BEA brand assets so the spike video looks like BEA, not generic.

## What's needed

| File | What it is | Required for spike? |
|---|---|---|
| `theme.json` | Brand config (colors, fonts, voice) | Yes — already exists as a placeholder, fill in the real values |
| `logo.png` | BEA logo, PNG, transparent background, ≥ 512×512 | Yes |
| `intro.mp4` | 2-second branded intro video | Optional — leave empty if not ready, the renderer can generate a default |
| `outro.mp4` | 2-second branded outro video | Optional — same |
| `bg_music.mp3` | Optional background bed | No — skip for spike |

## How to fill in `theme.json`

| Field | What to put |
|---|---|
| `primary_color` | Main brand color, hex |
| `secondary_color` | Secondary brand color, hex |
| `accent_color` | Used for highlights / emphasis text |
| `background_color` | Slide background |
| `font_heading` | Heading font name — if a custom font, drop the .ttf/.otf next to this file and reference it by filename |
| `font_body` | Body font name, same |
| `voice` | TTS voice identifier. The exact format depends on what `training-video-generator` uses — check its README. Common options: ElevenLabs voice ID, Google TTS voice name, Azure neural voice. |
| `intro_seconds` / `outro_seconds` | Length of branded book-ends if generated dynamically |
| `video.resolution` | `1920x1080` is the safe default. `1080x1920` if targeting vertical / mobile-first viewing. |
| `video.fps` | 30 is fine. 60 if the team prefers. |

## A note on voice

For the spike, picking a voice quickly matters more than picking the *right* voice. Use whatever default `training-video-generator` ships with on Day 2, then iterate post-spike. The decision-memo evaluation (Day 3) will tell you if voice is a top-3 problem worth solving.

## Don't commit secret keys

If `training-video-generator` needs ElevenLabs or another paid-TTS key, put it in `.env`, not in `theme.json`. The theme is committed to git; the env is not.
