# BEA Training Engine — Google APIs Inventory

> Mapping each pipeline step to the most relevant Google APIs. BEA already has Google Cloud + NotebookLM Enterprise + a YouTube channel, so most additions reuse the same auth (`gcloud` ADC or YouTube OAuth) and the same billing relationship.

---

## Pipeline ↔ Google APIs

| Pipeline step | Already in plan | Google API option | Status |
|---|---|---|---|
| Source ingestion (notebook + RAG) | ✅ NotebookLM Enterprise | Discovery Engine (NotebookLM Enterprise) | In use |
| Audio overview / podcast | ✅ NotebookLM Enterprise | NotebookLM `audioOverviews` | In use |
| Slide outline + narration | Claude (Anthropic) | **Vertex AI Gemini** (alternative) | Consider |
| TTS narration | Kokoro (local, default) | **Cloud Text-to-Speech** (opt-in) | Already wired |
| Slide image rendering | PIL/Pillow | Imagen 3 (Vertex AI) — for AI-generated visuals | Phase 2 |
| Video assembly | ffmpeg (local) | — no good Google API alternative for assembly | — |
| Thumbnails | YouTube-Thumbnail repo | Imagen 3 — alternative for AI thumbnails | Phase 2 |
| Captions / subtitles | SRT from narration | YouTube `captions.insert` | **Add** |
| YouTube upload | TODO | **YouTube Data API v3** | **Add** |
| Translation (multilingual) | Not planned for v1 | **Cloud Translation API** | Q4 — Phase 2 |
| Backup storage | TODO | **Cloud Storage** (GCS) or stick with R2 | Decide |
| Analytics on training effectiveness | Toklytics tracks playback | **YouTube Analytics API** + **YouTube Reporting API** | **Add** |
| Content moderation | Not planned | Cloud Video Intelligence API | Phase 2 |
| Pre-upload script safety check | Not planned | Cloud Natural Language API | Phase 2 |
| Orchestration / scheduling | Not designed | Cloud Workflows + Cloud Run + Cloud Scheduler | Phase 1 (or stick with Cloudflare Workers) |

---

## Tier 1 — Add to Phase 1 plan

### YouTube Data API v3 (required, blocking)

The single API that gets us from MP4 to "video lives on @boldevolution".

| Method | Purpose |
|---|---|
| `videos.insert` | Upload the MP4. Set `privacyStatus: "unlisted"`, `madeForKids: false`, `defaultLanguage: "en"`, AI-content disclosure flag |
| `thumbnails.set` | Attach custom thumbnail from `YouTube-Thumbnail` repo |
| `captions.insert` | Upload SRT captions (English first, more languages later) |
| `playlists.insert` / `playlistItems.insert` | Organize modules into series (e.g., "Gifting 101", "Compliance Essentials") |
| `videos.update` | Edit metadata after publish (description tweaks, tag updates) — does NOT replace the file |

**Auth:** OAuth 2.0 with `https://www.googleapis.com/auth/youtube.upload` scope. One-time consent by a channel admin; refresh token stored server-side.

**Quota:** Default 10,000 units/day. `videos.insert` costs ~1,600 units. ~6 uploads/day default; request increase if batch-rendering a back catalog. [Quota docs](https://developers.google.com/youtube/v3/getting-started#quota).

**Python SDK:** `google-api-python-client` — well-supported, idiomatic.

### YouTube Analytics API (Phase 1)

Toklytics-LiveIQ already tracks in-app playback. **YouTube Analytics adds the complementary view: how creators behave when watching outside Toklytics** (forwarded links, embedded elsewhere).

| Method | Purpose |
|---|---|
| `reports.query` | Per-video stats: views, average view duration, audience retention curve |

Combined with Toklytics's in-app tracking, you get a complete picture of training engagement.

**Auth:** Same OAuth as Data API, scope `https://www.googleapis.com/auth/yt-analytics.readonly`.

### Cloud Text-to-Speech (already opt-in)

Already wired into the spike via `TTS_ENGINE=gcloud`. Switch from Kokoro when Phase 1 needs production-grade voice.

**Voice recommendation:** `en-US-Studio-O` (female, natural) or `en-US-Studio-Q` (male, natural). Studio voices are higher quality than Wavenet, cost ~4x more, worth it for production training.

**Cost:** ~$16 per 1M characters with Studio voices. A 90-second video at ~150 wpm = ~225 words = ~1,200 characters = ~$0.02. Negligible at BEA's volume.

---

## Tier 2 — Consider for Phase 1 / 2

### Vertex AI Gemini (alternative to Claude for slide derivation)

**Tradeoffs vs Claude:**

| Dimension | Claude (current default) | Vertex AI Gemini |
|---|---|---|
| Output quality for structured generation | Excellent | Comparable for this task |
| Same vendor as NotebookLM | No | Yes — same Google Cloud project, same billing |
| Auth | Separate API key | Same `gcloud` ADC as NotebookLM |
| Long context | 1M tokens (Sonnet 4.6/4.7) | 1M tokens (Gemini 1.5 Pro), 2M (Gemini 2.0+) |
| Cost | $3-15 per million input/output | $1.25-5 per million (Gemini 1.5 Pro) |

**Recommendation:** Stick with Claude for the spike (already wired, strong on this kind of structured + tonal task). Consider Gemini as a Phase 1 optimization if cost or auth simplification matters. The `slide_deriver.py` interface is small enough to swap.

### Cloud Translation API (multilingual training, Phase 2)

If/when BEA wants Spanish, Portuguese, Tagalog, etc. variants:

1. Translate the narration JSON (slide-by-slide narration text) via `translateText`
2. Re-run TTS with a target-language voice
3. Re-render video with same slides + new audio
4. Upload as a new module in the target language

[NMT model](https://cloud.google.com/translate/docs/advanced/translating-text-v3) is mature; quality is good for creator coaching content.

**Cost:** $20 per million characters. ~1,200 chars per video = ~$0.024 per language per video. Trivial.

### Cloud Storage (backup) vs Cloudflare R2

| | GCS | R2 |
|---|---|---|
| Same vendor as everything else in pipeline | ✅ | ❌ (Cloudflare) |
| Egress cost | Standard | Zero |
| Already in BEA stack | Yes (NotebookLM lives on GCP) | Yes (KLING-Director's hosting referenced Cloudflare) |

**Recommendation:** R2 for archive (zero egress is meaningful for video files), GCS only if a Phase 1 orchestration step needs to read the MP4 from inside GCP services.

---

## Tier 3 — Defer

### Imagen 3 (AI-generated slide images / thumbnails)

Could replace PIL slide rendering with AI-generated visuals per slide. **Probably wrong for Phase 1** — training videos need *consistent* visual style across modules, and AI image gen is famously inconsistent unless tightly prompted. Better suited to:
- Hero / cover images for module catalog (one-shot per module, human-reviewed)
- Background imagery behind slide text (one per module, reused across slides)

Defer to Phase 2 once the pipeline is stable.

### Cloud Video Intelligence API (pre-upload content moderation)

Scans uploaded videos for explicit content, brand safety issues, etc. For AI-generated training, the risk is low — but if BEA scales to N creators submitting their own segments, this becomes the moderation backbone. Defer.

### Cloud Natural Language API (pre-upload script safety)

Scan the generated narration text for sentiment, entities, claim-likely-to-be-flagged-by-TikTok-ToS phrases. **Probably overkill** — better solved by a Claude/Gemini "review pass" prompt in `slide_deriver.py` than by a dedicated API. Defer or skip.

### Cloud Workflows + Cloud Run

Serverless orchestration if Phase 1 needs scheduled or event-driven generation. **Probably skip** — BEA's existing stack (Cloudflare Workers, Vercel, Railway) is sufficient for the engine's orchestration needs. Adopting GCP orchestration adds vendor sprawl without clear payoff.

---

## Auth model with full Google API adoption

Two distinct auth surfaces:

1. **Server-to-server (ADC / service account):** NotebookLM Enterprise, Vertex AI Gemini, Cloud TTS, Cloud Translation, Cloud Storage, Imagen, Cloud Video Intelligence
2. **Per-user OAuth (refresh token):** YouTube Data API, YouTube Analytics API — must be authorized by a channel admin once, refresh token stored

A single GCP service account handles (1); a single OAuth refresh token for the @boldevolution channel handles (2). Document both in a `secrets/` README so onboarding new engineers is straightforward.

---

## Cost ballpark — full Google-API stack, per video

| Step | API | Cost per 90s video |
|---|---|---|
| NotebookLM audio overview | Discovery Engine | Bundled with Enterprise license |
| Slide derivation (Gemini 1.5 Pro alternative) | Vertex AI | ~$0.01 |
| TTS (Studio voice) | Cloud TTS | ~$0.02 |
| YouTube upload | Data API | Free (within quota) |
| YouTube Analytics | Analytics API | Free |
| Caption upload | Data API | Free (within quota) |
| Translation (if multilingual) | Translation API | ~$0.02 per language |
| **Total per English video** | | **~$0.03 + Enterprise license amortized** |
| **Total per multilingual variant** | | **~$0.05 per language** |

Compare to alternative stacks (Synthesia ~$10/video, HeyGen ~$5/video). Even at 10x BEA's current volume, the Google-API stack is dramatically cheaper.

---

## Recommendation

For Phase 1, adopt:

1. **YouTube Data API v3** — required, blocking the upload path
2. **YouTube Analytics API** — adds the off-app engagement view
3. **Cloud Text-to-Speech (Studio voices)** — production-grade voice quality

Keep open:

4. **Vertex AI Gemini** — evaluate Phase 1 if cost or vendor consolidation matters more than current Claude quality
5. **Cloud Translation** — Phase 2 if/when languages beyond English become scope

Defer:

6. Imagen, Cloud Video Intelligence, Cloud Natural Language, Cloud Workflows — wait for a concrete need.

---

## References

- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [YouTube Data API quota](https://developers.google.com/youtube/v3/getting-started#quota)
- [YouTube Analytics API](https://developers.google.com/youtube/analytics)
- [Cloud Text-to-Speech voices](https://cloud.google.com/text-to-speech/docs/voices)
- [Vertex AI Gemini API](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models)
- [Cloud Translation API](https://cloud.google.com/translate/docs)
- [NotebookLM Enterprise API root](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)
