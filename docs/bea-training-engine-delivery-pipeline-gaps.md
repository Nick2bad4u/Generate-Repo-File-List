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
- Privacy: **Unlisted** (confirmed by BEA). Anyone with the link / embed can play; not searchable on YouTube; not visible on the channel page. The Toklytics-LiveIQ iframe embed is the only intended access path.
- Chapter markers for navigability
- End screens / cards optional

**Recommendation:** Use the existing `YouTube-Thumbnail` repo as the thumbnail step. Add a new `youtube_publisher.py` to the engine for upload. Single channel, unlisted by default, Public for select training that doubles as marketing.

### 2. Toklytics-LiveIQ video module — ✅ RESOLVED
**Status:** Already in place. BEA confirmed the Training structure exists in Toklytics-LiveIQ.

**Integration mechanism:** **YouTube playlists** are the handoff. Toklytics-LiveIQ reads the @boldevolution training playlists and presents them in the app. The engine just needs to:
1. Upload the MP4 to YouTube (unlisted)
2. Add it to the correct training playlist for that module's language / topic
3. Toklytics auto-discovers the new video on its next playlist sync

**No DB write, no tRPC, no separate manifest needed.** This is dramatically simpler than the schema-based integration originally assumed.

Implementation: `youtube_publisher.py` accepts a `playlist_id` per call. The orchestrator's `publish-youtube` command resolves it via a fallback chain (CLI flag → module JSON → env var per language). `list-playlists` CLI command helps find the right IDs during setup.

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

### 6. Video metadata manifest — ✅ NOT NEEDED
**Status:** Made obsolete by the playlist-based handoff. All module metadata that Toklytics-LiveIQ needs lives on the YouTube video itself (title, description, tags, category, thumbnail, captions) + the playlist membership tells Toklytics which catalog section to put it in. No separate manifest record required.

**Engine-internal tracking:** Module status, prompt template version, source commit SHA, cost, and audit log live in the engine's own state file (`outputs/review-state.json` during the spike; a real DB in Phase 1). These are operational metadata Toklytics doesn't need to see.

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

### 9. Editorial / approval workflow — ✅ DESIGNED
**Status:** Full design in `bea-training-engine-editorial-workflow.md`. Engine-side scaffold (state machine + CLI for review/approve/reject/request-changes/publish-gate) shipped in `bea-training-engine-spike/src/module_status.py` + orchestrator commands. The Toklytics-LiveIQ admin dashboard is the remaining implementation work (estimated 5-7 days for the LiveIQ team).

### 10. Notifications when new modules drop
**Status:** Mentioned in the spec architecture but not implemented.

**What's needed:**
- In-app notification in Toklytics-LiveIQ ("New training: Acknowledging gifters")
- Optional: email or push if Toklytics ships those channels
- Quiet-window logic so creators don't get spammed (one digest per week, not per-video pings)

---

## Tier 3 — Nice to have, defer

### 11. Discoverability / SEO — ❌ OUT OF SCOPE
- All training is unlisted per BEA. No public-search surface, no SEO concerns.
- One small implication: video titles / descriptions can be optimized for the **in-app catalog** (Toklytics Training tab) instead of YouTube search — different copywriting target.

### 12. Multi-language localization — ⬆️ PROMOTED to Phase 1
- Spanish (es-US) is in scope per BEA. Spec: translate narration + on-screen text via Cloud Translation API, render with Cloud TTS Spanish voice, publish as a separate YouTube video.
- Glossary in `translator.py` keeps TikTok product names ("Lion", "Universe", "Gift", "Battle"), platform names ("TikTok LIVE"), and BEA brand terms untranslated.
- Other languages (Portuguese-BR, Tagalog, etc.) are mechanically identical — change the target code and add a voice mapping in `brand/theme.json`. Defer until Spanish is validated.

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

1. ~~**One YouTube channel or separate?**~~ **Resolved:** single channel — [@boldevolution](https://youtube.com/@boldevolution), "Bold Evolution Agency". Same channel hosts both public-facing content (if any) and unlisted training. Unlisted videos don't show on the channel page, so there's no UX conflict.
2. ~~**Unlisted only, or some public training that doubles as marketing?**~~ **Resolved:** unlisted only.
3. ~~**What's the editorial review bar?**~~ **Resolved:** Per-video at launch (Phase 1). Per-batch as a Phase 2 optimization once a prompt-template family has shipped 50+ modules with < 10% rejection rate. Compliance-flagged modules (keyword heuristic + senior editor co-sign) get extra scrutiny. Spike-side scaffold lives in `bea-training-engine-spike/src/module_status.py`; full design in `docs/bea-training-engine-editorial-workflow.md`.
4. ~~**Languages beyond English in scope for v1?**~~ **Resolved:** Spanish (es-US Latin American Spanish, the largest Spanish-speaking TikTok creator market). Implemented via Cloud Translation API + Cloud TTS Spanish voices. See `bea-training-engine-spike/src/translator.py` + `translate-deck` orchestrator command. Each module renders twice (English + Spanish) and publishes as two separate YouTube videos with appropriate `defaultLanguage`/`defaultAudioLanguage` metadata.
5. ~~**Is Toklytics-LiveIQ ready to host a Training tab?**~~ **Resolved:** structure already in place. Engine needs to learn its schema.
6. ~~**Branding — "BEA" or sub-brand?**~~ **Resolved:** full name "Bold Evolution Agency" (not "BEA Academy" or similar). Affects:
    - Video upload metadata: description prefix references "Bold Evolution Agency creator training"
    - Video lower-thirds / outro slide say "Bold Evolution Agency"
    - AI-content disclosure wording: "Narration AI-generated. Content sourced from Bold Evolution Agency creator coaching materials."
7. **Do creators expect access to past training in perpetuity, or does retention follow Toklytics-LiveIQ's tier-based retention (14/30/90 days from KLING-Director's pricing)?**

### Implications of unlisted-only
- No public marketing value from the videos themselves — Toklytics-LiveIQ is the only intended player
- Channel branding matters less (creators don't visit the channel page)
- Comments on YouTube can be disabled at upload time (no public engagement layer anyway)
- The YouTube channel becomes essentially a content storage + delivery CDN; the catalog/UX lives entirely in Toklytics-LiveIQ
- If a video URL leaks (forwarded, shared), anyone can play it — no auth wall on YouTube itself. The proprietary moat is the *curation + coaching loop in Toklytics*, not the videos themselves
