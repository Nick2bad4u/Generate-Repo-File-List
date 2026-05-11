# BEA Training Engine — Tooling Findings

> Captured during Phase 0 spike scaffolding, before runtime verification.
> Date: 2026-05-11
> Status: Important course corrections to the original spec.

---

## TL;DR

Two assumptions in the original `bea-training-engine-spec.md` turned out to be wrong:

1. **NotebookLM Enterprise API does *not* expose video overview generation.** It exposes audio overviews and podcasts only. The "video overview" feature exists in consumer NotebookLM's Studio UI but isn't an API endpoint we can call.
2. **`training-video-generator` (the BEA fork) is *not* a slide-deck-to-MP4 renderer.** It's a tutorial-recording tool that captures screenshots + AI narration and exports a Google Doc, expecting a human to upload it to NotebookLM's Studio UI and click "Generate Video."

The original pipeline assumed: `NotebookLM → slides+narration → training-video-generator → MP4`. That pipeline doesn't exist as designed. We need to either pick a different stack or accept manual UI steps.

---

## What we verified

### NotebookLM Enterprise API surface

Official docs: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks

| Capability | API support? | Notes |
|---|---|---|
| Notebook CRUD | ✅ | `notebooks.create / get / listRecentlyViewed / batchDelete / share` |
| Source upload (text, web, YouTube) | ✅ | `notebooks/{id}/sources:batchCreate` |
| Source upload (PDF/DOCX/PPTX/MP3/etc.) | ⚠️ | `uploadFile` method exists; wire format not documented on the page we read |
| **Audio overview generation** | ✅ | `audioOverviews.create` — async, takes a few minutes |
| **Audio overview retrieval (audio + transcript)** | ❓ | Docs page describes create + delete + UI playback. Whether the API returns the audio file URL or transcript is the **highest-priority Day 1 unknown**. |
| **Podcast generation** | ✅ | Separate endpoint, not yet investigated. Likely a richer multi-speaker variant of audio overview. |
| **Video overview generation** | ❌ | Not a documented API method. Consumer NotebookLM UI has it; Enterprise API doesn't expose it. |
| Slide deck generation | ❌ | Never an API output. |
| Briefing doc / study guide / FAQ / mind map | ❌ | Not documented in the Enterprise API as of the docs page we read. |

**Implication:** the API gives us a strong RAG-grounded **audio** path, but no native API path to a finished video.

### `training-video-generator` fork

Repo: https://github.com/BEA-BOLD-EVOLUTION/training-video-generator
Upstream: https://github.com/3thirty3gitter/training-video-generator

This is a **Next.js web tool** that runs at `localhost:3000` (`npm run dev`). It does *not* expose a CLI or library API for our orchestrator to call.

**What it actually does:**
1. User defines tutorial steps in the web UI
2. Tool captures screenshots of an external app via browser automation
3. Adds AI-generated narration text (Gemini API optional)
4. Exports a Google Doc / PDF
5. **User uploads the Doc to NotebookLM Studio UI and clicks "Generate Video"**

There's a `generate_kokoro.py` Python helper for TTS using the [Kokoro](https://github.com/hexgrad/kokoro) open-source model — that's the only Python piece, and it's narration-only, not video assembly.

**Implication:** this fork doesn't fit the "deck JSON → MP4" role we wrote into the spike. It also doesn't match BEA's primary use case: BEA isn't generating SaaS-screenshot tutorials; BEA is generating creator-coaching content from existing source docs.

---

## Three viable spike pipelines now

| Path | Stack | Pros | Cons |
|---|---|---|---|
| **A. DIY video assembly** (recommended for spike) | Enterprise API audio overview (if retrievable) **OR** Kokoro TTS for narration → PIL/Pillow for slide images → ffmpeg for assembly | Fully automated. No UI clicks. Works without consumer NotebookLM. Hits the Phase 0 success criterion ("watchable end-to-end"). | Slide design is basic; voice may feel less natural than NotebookLM podcast voices. |
| **B. Consumer NotebookLM Video Overview, manual** | Enterprise API for sources → switch to consumer NotebookLM UI → click "Video Overview" → download | Highest output quality available today. Native NotebookLM voices + slide design. | UI steps. Doesn't automate. Different account from Enterprise. Not a viable Phase 1 if we want a hands-off pipeline. |
| **C. SaaS video gen (Synthesia / HeyGen / RunwayML)** | Enterprise API audio overview for narration → SaaS for avatar + slides → MP4 | Production-grade output. Cleanest brand control. | Cost: $1-10+ per video. New vendor relationship. Some have humanoid avatars BEA may not want. |

**Recommendation: build Path A for the spike.** It's the only path that proves an end-to-end automated pipeline. If quality is the only blocker after Day 3, Path C becomes the Phase 1 upgrade.

---

## Concrete Path A pipeline

```
┌────────────────────────────────────────────────────────────────┐
│  SOURCE DOCS (BEA-Live-Guide, LMS, etc.)                       │
└──────────────────────────────┬─────────────────────────────────┘
                               ↓
            ┌──────────────────────────────────┐
            │  NotebookLM Enterprise           │
            │  (Audio overview if retrievable, │
            │   else just RAG context)         │
            └──────────────────┬───────────────┘
                               ↓
            ┌──────────────────────────────────┐
            │  Claude (slide_deriver.py)       │
            │  → deck.json (slides + narration)│
            └──────────────────┬───────────────┘
                               ↓
       ┌───────────────────────┼───────────────────────┐
       ↓                       ↓                       ↓
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ PIL renders  │       │ Kokoro TTS   │       │ Brand assets │
│ slide images │       │ per-slide    │       │ (logo,       │
│ (PNG)        │       │ narration    │       │  colors)     │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       └───────────────────────┼───────────────────────┘
                               ↓
                    ┌────────────────────┐
                    │  ffmpeg assembly   │
                    │  → 01-video-spike.mp4
                    └────────────────────┘
```

**Why this works:**
- Every step is automated and locally runnable
- Quality is "basic but watchable" — meets Phase 0 bar
- All the hard parts (Claude derivation, brand application) have clear seams for Phase 1 upgrades
- If audio-overview retrieval works, swap Kokoro for the NotebookLM voice; otherwise Kokoro is the fallback

---

## What the spike kit changes

Before this finding:
- `video_renderer.py` was a TODO stub assuming `training-video-generator` could do `deck.json → MP4`

After this finding:
- `video_renderer.py` becomes a real implementation: PIL → Kokoro → ffmpeg
- New `tts_client.py` for the Kokoro wrapper
- `requirements.txt` adds Pillow + kokoro-onnx (or similar)
- `setup.sh` checks for ffmpeg
- `training-video-generator` fork stays cloned but **becomes optional / reference-only**, not part of the spike's hot path

---

## Open questions (Day 1 will answer)

1. **Can we retrieve the audio overview audio file via API?** If yes, the spike video uses NotebookLM's voice. If no, Kokoro takes over.
2. **Can we retrieve the audio overview transcript via API?** If yes, Claude has both transcript + sources for slide derivation. If no, Claude works from sources only.
3. **What's `uploadFile`'s wire format?** Needed for PDF sources. Workaround: convert PDFs to .md for the spike.
4. **Is Kokoro voice quality acceptable for BEA?** Day 3 evaluation answers this.

---

## What this means for the main spec

The main `bea-training-engine-spec.md` needs updates for Phase 1:

- §4.4 ("Video production — `training-video-generator`") needs a rewrite. The fork doesn't do what we thought.
- The Phase 1 architecture should plan for the DIY assembly approach OR commit to a Path C SaaS vendor.
- Personalization (V2) gets cheaper with a DIY pipeline since per-creator runs don't pay per-video API fees.

I'll defer the spec rewrite until after the spike's Day 3 decision memo — no point rewriting the spec twice if Day 3 surfaces new info.

---

## References

- NotebookLM Enterprise API root: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks
- Sources API: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources
- Audio overview API: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-audio-overview
- training-video-generator (BEA fork): https://github.com/BEA-BOLD-EVOLUTION/training-video-generator
- training-video-generator (upstream): https://github.com/3thirty3gitter/training-video-generator
- Kokoro TTS: https://github.com/hexgrad/kokoro
