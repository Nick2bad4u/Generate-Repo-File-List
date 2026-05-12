# BEA Training Engine — Delivery Pipeline Gaps

> Context update: BEA training videos will be **hosted on YouTube** and **played inside the Toklytics-LiveIQ app**. The current spec/kit produces an MP4 and stops there. This doc inventories what's missing on the back half of the pipeline.

---

## The full pipeline (revised)

```
Sources → NotebookLM → Claude → PIL/TTS/ffmpeg → MP4
                                                   │
                                                   ↓
                                          ┌────────────────┐
                                          │  Thumbnail      │ ← YouTube-Thumbnail repo
                                          │  Captions       │ ← Whisper from narration
                                          │  Metadata       │ ← title, desc, tags, chapters
                                          └────────┬────────┘
                                                   ↓
                                          ┌────────────────┐
                                          │  YouTube upload │ ← Data API v3 OAuth
                                          │  (unlisted)     │
                                          └────────┬────────┘
                                                   ↓
                                          ┌────────────────┐
                                          │  Video manifest │ ← module ID, video ID,
                                          │  in Toklytics DB│   tags, audience, region
                                          └────────┬────────┘
                                                   ↓
                                          ┌────────────────┐
                                          │  In-app player │ ← YouTube iframe or
                                          │  + completion  │   IFrame API for events
                                          │  tracking      │
                                          └────────┬────────┘
                                                   ↓
                                          ┌────────────────┐
                                          │  Analytics +   │ ← watched / dropped / completion
                                          │  coaching loop │   feeds back into per-creator
                                          │                │   Toklytics insights
                                          └────────────────┘
```

---

## Tier 1 — Must address before launch

### 1. YouTube upload automation
**Status:** Not in spike kit or spec. Manual upload is fine for spike, blocks Phase 1.

**What's needed:**
- YouTube Data API v3 integration (OAuth 2.0, channel auth)
- A dedicated BEA YouTube channel (or sub-channel) — decision needed: one channel for all training, separate from any consumer-facing BEA channel
- Upload script with metadata: title, description, tags, category, language, default audience (Kids: No), made for kids: No
- **AI-content disclosure** — YouTube requires creators to disclose "altered or synthetic content that seems realistic" for some categories. AI-narrated training likely qualifies. This is a checkbox in the upload metadata; getting it wrong is a strike risk.
- Privacy: **Unlisted** by default (only people with the link / embed can play), not Private (which blocks embedding), not Public (creates a public-search SEO surface that may not be wanted for proprietary training).
- Chapter markers for navigability
- End screens / cards optional

**Recommendation:** Use the existing `YouTube-Thumbnail` repo as the thumbnail step. Add a new `youtube_publisher.py` to the engine for upload. Single channel, unlisted by default, Public for select training that doubles as marketing.

### 2. Toklytics-LiveIQ video module — ✅ RESOLVED
**Status:** Already in place. BEA confirmed the Training structure exists in Toklytics-LiveIQ.

**Remaining work** (engine-side, not LiveIQ-side):
- Get the exact schema the engine should write into (table name, required fields, video reference format — embedded URL vs YouTube ID vs module ID)
- Confirm how completion events flow (does the iframe already wire YouTube IFrame API events into LiveIQ tracking?)
- Define the API or DB contract: how does the engine create a new module record after publishing to YouTube?

### 3. Thumbnails wired into the pipeline
**Status:** Repo exists (`YouTube-Thumbnail`) but not connected.

**What's needed:**
- Inspect the existing repo's API/CLI
- Call it from the orchestrator after the MP4 is rendered, passing: title text, BEA brand colors, optional creator name or topic
- Output: PNG matching YouTube's required dimensions (1280×720, < 2MB, JPG/PNG/GIF/BMP)
- Auto-attach during YouTube upload

### 4. Captions / subtitles
**Status:** Not in spec. Creator network is global; UK / US / CA at minimum; many non-native English speakers.

**What's needed:**
- Generate SRT from the narration text we already have (we wrote it, we know exact timing per slide)
- Skip Whisper — we know what was said, no need to transcribe
- Upload SRT alongside the video via YouTube Data API
- Optional: machine-translate to other languages (Spanish, Portuguese, others depending on creator regions)

**Recommendation:** This is a 1-day add. The narration timing is already known from the ffmpeg step.

### 5. AI-generated content disclosure
**Status:** Not addressed. YouTube ToS + FTC implications.

**What's needed:**
- Disclose in video description: *"Narration in this video was AI-generated. Content is sourced from Bold Evolution Agency creator coaching materials."*
- Set the YouTube "altered content" flag in upload metadata where appropriate
- Set "made for kids" to No
- TikTok-adjacent content: avoid claims that could be construed as platform manipulation tutorials

---

## Tier 2 — Important, should address in Phase 1

### 6. Video metadata manifest — ✅ LIKELY RESOLVED
**Status:** Toklytics-LiveIQ already has the Training structure, which presumably implies a module schema. Engine needs to write into that existing schema rather than define its own.

**Remaining work:**
- Document the Toklytics module schema as it exists today (field-by-field)
- Adapt the engine to produce records that fit — including any fields not in the suggested list below
- Suggested fields the engine *can* contribute (so LiveIQ doesn't have to ask):

```
module
├── id (BEA-TRN-0001, etc.)
├── title
├── description
├── youtube_video_id
├── duration_seconds
├── topic_tags (gifting, retention, compliance, etc.)
├── audience_tier / audience_region
├── source_version (which BEA-Live-Guide commit produced this)
├── published_at
├── ai_generated: bool
└── prerequisites: [module_id...]
```

If LiveIQ's existing schema is leaner, the extras live in the engine's own DB and we expose them via a separate manifest endpoint if needed.

### 7. Completion tracking + coaching loop — ⚠️ PARTIALLY RESOLVED
**Status:** Toklytics-LiveIQ's Training structure presumably already tracks playback. The coaching-loop integration (using watched-module data inside the realtime coach) is the remaining Phase 2 piece.

**Remaining work:**
- Confirm watched-event schema in Toklytics
- Phase 2: surface "creator X watched module Y N days ago, behavior on metric Z changed by W%" as a signal to the Live Coach

### 8. Versioning and re-rendering
**Status:** Not addressed. Source docs change; training drifts.

**What's needed:**
- Each module records the source commit SHA that produced it
- A "stale" flag when sources change beyond N% similarity
- Choice: re-upload to YouTube as a new video (new URL, lose stats), OR re-render and update via YouTube's "Replace Video" (limited; preserves URL/stats but Data API may not expose it). YouTube generally doesn't let you replace the video file itself — you'd need to delete + reupload + relink in Toklytics
- Recommendation: treat re-renders as new modules with versioned IDs (`BEA-TRN-0001-v2`) and let creators see "newer version available"

### 9. Editorial / approval workflow
**Status:** Not addressed. AI-generated training that auto-publishes is a risk.

**What's needed:**
- A staging step: generated video → reviewer dashboard → approve → publish
- Reviewer dashboard (likely a Toklytics admin screen) with: preview player, source citations, AI-generation note, approve / reject / send-back buttons
- Audit log of who approved what

**Recommendation:** Required for Phase 1 launch even if it's just "Tobi or someone on the team clicks approve in a UI."

### 10. Notifications when new modules drop
**Status:** Mentioned in the spec architecture but not implemented.

**What's needed:**
- In-app notification in Toklytics-LiveIQ ("New training: Acknowledging gifters")
- Optional: email or push if Toklytics ships those channels
- Quiet-window logic so creators don't get spammed (one digest per week, not per-video pings)

---

## Tier 3 — Nice to have, defer

### 11. Discoverability / SEO (only if some training is public)
- Public training videos can double as marketing for the agency. Title / description / tags / playlists / end-screens matter.
- If everything stays unlisted, skip this entirely.

### 12. Multi-language localization
- DeepL / Google Translate the narration text, regenerate audio in the target language, render new video. Same pipeline, different language input. Phase 2.

### 13. YouTube Shorts cuts
- Vertical 9:16 30-second teasers from each module. Promotional reach. Phase 2.

### 14. Quizzes / interactive elements
- LMS-style "did you understand?" checks after each video. Cards + endscreens link to a Toklytics quiz page. Phase 2.

### 15. A/B testing
- Two narration variants for the same module to test creator behavior change. Phase 3.

### 16. Music licensing (intro / outro)
- If BEA wants branded audio book-ends, source from royalty-free libraries (Epidemic Sound, Artlist, YouTube Audio Library). Avoid Content ID issues.

### 17. Cost tracking
- Per-video API spend rollup (NotebookLM Enterprise + Claude + TTS + YouTube quota). One dashboard row per render.

### 18. Backup / archive
- R2 backup of every MP4 alongside the YouTube copy. Defense against channel takedown / accidental delete.

### 19. Content moderation policy
- Pre-approval checklist before any AI-generated training claims something about TikTok mechanics. "Does this claim violate TikTok ToS?" filter.

### 20. Watermarking (proprietary content protection)
- Subtle BEA watermark + creator-specific watermark for highly proprietary modules. Phase 2.

---

## Suggested order of execution

**Spike (Phase 0):**
- Current kit through MP4 — already done
- Add: thumbnail integration (1-day add since the repo exists)
- Add: SRT generation from narration (1-day add)

**Phase 1 (3-4 weeks after spike succeeds):**
- YouTube upload automation (Tier 1 #1) ← biggest remaining gap
- Adapter writing into Toklytics-LiveIQ's existing Training schema (Tier 2 #6 — schema discovery first)
- AI-content disclosure (Tier 1 #5) — quick policy decision
- Editorial / approval workflow (Tier 2 #9)
- Thumbnail wiring (Tier 1 #3) — fast since the repo already exists
- SRT captions from narration (Tier 1 #4) — 1-day add

**Phase 2 (4-6 weeks):**
- Completion tracking + coaching loop (Tier 2 #7)
- Notifications (Tier 2 #10)
- Versioning (Tier 2 #8)
- Per-creator personalization (existing V2 plan from main spec)

**Phase 3 (ongoing):**
- Tier 3 items based on traction

---

## Open questions for BEA

1. **One YouTube channel for everything, or separate channels?** (e.g., one for public marketing content, one for unlisted training)
2. **Unlisted only, or some public training that doubles as marketing?**
3. **What's the editorial review bar?** Per-video approval, or per-batch?
4. **Languages beyond English in scope for v1?**
5. **Is Toklytics-LiveIQ ready to host a Training tab, or does that need its own product spike first?**
6. **Branding — is this content from "BEA" the agency, or a sub-brand like "BEA Academy" / "Creator U"?** (Affects channel name, video branding, AI-disclosure wording)
7. **Do creators expect access to past training in perpetuity, or does retention follow Toklytics-LiveIQ's tier-based retention (14/30/90 days from KLING-Director's pricing)?**
