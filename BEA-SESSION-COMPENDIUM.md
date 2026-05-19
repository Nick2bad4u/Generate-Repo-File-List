# BEA — Session Compendium

> Consolidated master document. Everything produced this session in one file.
> Branch: `claude/setup-repo-execution-dXbhZ`
> Generated: 2026-05-19

This single document concatenates all design docs produced during the BEA
strategy + build session. Source-of-truth copies live in `docs/` and the
working code lives in `bea-training-engine-spike/`. This compendium is for
reading / sharing / offline review.

---

## Table of contents

### Part I — BEA Training Engine (the main build)

1. [Design Spec](#1-design-spec)
2. [Quality Strategy (production north star)](#2-quality-strategy)
3. [Pedagogy (content north star)](#3-pedagogy)
4. [Remotion Architecture](#4-remotion-architecture)
5. [Phase 0 Spike Runbook](#5-phase-0-spike-runbook)
6. [Tooling Findings](#6-tooling-findings)
7. [Delivery Pipeline Gaps](#7-delivery-pipeline-gaps)
8. [Editorial Approval Workflow](#8-editorial-approval-workflow)
9. [Google APIs Inventory](#9-google-apis-inventory)

### Part II — Adjacent agency work

10. [Toklytics-LiveIQ Security Audit](#10-toklytics-liveiq-security-audit)
11. [Toklytics-LiveIQ Mobile Wrapper](#11-toklytics-liveiq-mobile-wrapper)
12. [KLING-Director Security Audit](#12-kling-director-security-audit)
13. [KLING-Director Mobile Wrapper](#13-kling-director-mobile-wrapper)

### Part III — Code index

14. [Spike kit source files](#14-spike-kit-source-files)

---

## Status snapshot

| Item | State |
|---|---|
| Commits this session | 21 |
| Design docs | 13 |
| Spike kit source files | 12 |
| Logistics pipeline | Working scaffold, end-to-end |
| Pedagogy enforcement | 3 layers (prompt + runtime + editorial) |
| Spanish (es-US) variant | Wired |
| Remotion visual layer | Spec'd, not yet built |

### Open strategic choices

| # | Question | Status |
|---|---|---|
| 1 | Voice provider | ✅ Google Cloud TTS Studio |
| 2 | Visual framework | ✅ Remotion |
| 3 | Stock footage budget | ⬜ Open |
| 4 | Voice cloning vs pro voice | ✅ Pro voice |
| 5 | Flagship cadence | ⬜ Open |
| 6 | Content retention policy | ⬜ Open |

---


<a id="1-design-spec"></a>

# 1. Design Spec

> Source: `docs/bea-training-engine-spec.md`

---

# BEA Training Engine — Design Spec

> Working name: **bea-training-engine**
> Status: Draft v0.2
> Owner: Bold Evolution Agency
> **Quality bar:** see `bea-training-engine-quality-strategy.md` — that doc is the north star this spec serves. Phase 0's plain output is step 1 of the ladder, not the destination.

---

## 1. Vision

A pipeline that turns BEA's accumulated creator knowledge into **personalized training videos**, automatically — for use in the LMS, creator portals, and as direct creator coaching deliverables.

Topic in (or creator profile in) → finished MP4 + thumbnail + LMS module out, with minimal human authoring per video.

The engine leverages the NotebookLM ecosystem forks already in the BEA-BOLD-EVOLUTION account, combined with Claude orchestration and BEA's own knowledge base.

---

## 2. Success criteria

Hard quality gates (see `bea-training-engine-quality-strategy.md` for the full ladder):

| Metric | Floor (must clear) | Aspiration |
|---|---|---|
| Time from topic → published | < 1 day | < 1 hour |
| Cost per finished video | ≤ $5 in API/compute | ≤ $3 |
| Audience watch ratio at end | ≥ 50% | ≥ 75% |
| Creator-volunteer blind test | Can't distinguish AI-generated from team-produced on production quality | "Would screenshot/share unprompted" |
| Per-creator personalization (V2) | ≥ 3 data points from creator's last 30 days | Behavior change measurable in Toklytics for ≥ 30% of completions |
| Reuse rate | ≥ 5 variants per source module (regional, level, language) | n/a |

If a phase ships without clearing the floor row, that's a regression — do not promote to creators.

---

## 3. Architecture overview

```
┌────────────────────────────────────────────────────────────────┐
│  SOURCES                                                       │
│  - BEA-Live-Guide repo                                         │
│  - LMS repo content                                            │
│  - Portal docs (portal-uk, portal-us-ca, BEA_Creator_Portal)   │
│  - Toklytics historical reports (per creator)                  │
│  - Compliance docs                                             │
│  - Top creator transcripts (manual seed)                       │
└──────────────────────────────┬─────────────────────────────────┘
                               ↓
                      ┌────────────────┐
                      │  KNOWLEDGE     │
                      │   mybrain      │  fork: mybrain
                      │  (graph index) │
                      └────────┬───────┘
                               ↓
              ┌────────────────────────────────┐
              │  ORCHESTRATOR (Claude)         │
              │  - anthropic-sdk-typescript    │
              │  - claude-cookbooks (patterns) │
              │  - marketingskills (CRO/copy)  │
              │  - notebooklm-skill (planner)  │
              └────────────────┬───────────────┘
                               ↓
              ┌────────────────────────────────┐
              │  NOTEBOOKLM DRIVER             │
              │  - notebooklm-mcp-secure       │
              │  - notebooklm-py               │
              │  - Local-NotebookLM (fallback) │
              │  - awesome-notebookLM-prompts  │
              │  - notebooklm-prompts          │
              └────────────────┬───────────────┘
                               ↓
              ┌────────────────────────────────┐
              │  VIDEO PRODUCTION              │
              │  - training-video-generator    │
              │  (slides → MP4 with TTS)       │
              └────────────────┬───────────────┘
                               ↓
              ┌────────────────────────────────┐
              │  DISTRIBUTION                  │
              │  - YouTube-Thumbnail repo      │
              │  - LMS repo (auto-PR module)   │
              │  - Portals (creator dashboard) │
              └────────────────────────────────┘
```

---

## 4. Module breakdown

Each layer is owned by one or two forks. Forks are **integrated as git submodules** initially (so we can pull upstream updates) and only vendored if we diverge significantly.

### 4.1 Knowledge layer — `mybrain`

**What it does in upstream:** Turns folders of code, docs, papers, images, videos into a queryable knowledge graph.

**Role here:** The single source of truth about everything BEA knows. Ingests:

- All public repos (BEA-Live-Guide, LMS) on push
- Portal documentation
- Anonymized Toklytics report archive
- Compliance reference materials

**Why it matters:** Without this, every generation call starts from a blank context. With it, the orchestrator can answer "what does BEA actually teach about gifting strategy?" before drafting a slide.

**Integration risk:** Low — designed for exactly this use case.

---

### 4.2 Orchestration layer — Claude

**Forks:**

- `anthropic-sdk-typescript` — SDK
- `claude-cookbooks` — proven patterns (long context, tool use, structured output)
- `marketingskills` — CRO/copywriting/SEO/growth as composable skills
- `notebooklm-skill` — Claude skill that knows how to convert URLs/PDFs/topics into structured content

**Role here:** The brain. Given a generation request, it:

1. Queries `mybrain` for relevant BEA knowledge
2. Pulls creator-specific data from Toklytics (if personalized)
3. Composes a slide outline using prompt templates
4. Hands off to NotebookLM driver
5. Reviews the generated script for tone/accuracy
6. Triggers video production

**Design choice:** Use the Claude Agent SDK pattern (managed agent loop) rather than building a custom controller. Less code to maintain.

---

### 4.3 NotebookLM driver

**Forks:**

- `notebooklm-mcp-secure` — MCP server (hardened) so Claude can drive NotebookLM as a tool
- `notebooklm-py` — Python API for capabilities the web UI doesn't expose
- `Local-NotebookLM` — local alternative for privacy-sensitive creator data
- `awesome-notebookLM-prompts` + `notebooklm-prompts` — prompt template libraries

**Role here:** Turns a slide outline + source corpus into a finished slide deck and narration script.

**Two modes:**

| Mode | When | Stack |
|---|---|---|
| **Cloud** (default) | Public training content, regional variants | `notebooklm-mcp-secure` → `notebooklm-py` → Google NotebookLM |
| **Local** | Per-creator personalized videos (creator metrics are private) | `Local-NotebookLM` directly |

**Prompt library policy:** Maintain `prompts/` directory in this repo with the best templates curated from the two upstream prompt collections. Version-control them. A/B test variants.

---

### 4.4 Video production — `training-video-generator`

**What it does in upstream:** Automated SaaS training video generator built on top of NotebookLM. Takes the slide+script artifacts and produces a finished MP4.

**Role here:** Final mile. Input is the deck + narration; output is a polished video.

**Customizations expected:**

- BEA brand template (logo, color palette, fonts)
- Intro/outro scene with creator name (personalization)
- Lower-thirds for key tips (CTA)
- Optional captions track (use Whisper or NotebookLM-provided)

**Integration risk:** Medium — likely the fork most needing customization. Plan a v0 that uses defaults and a v1 that brands.

---

### 4.5 Distribution

**Forks/repos:**

- `YouTube-Thumbnail` (BEA repo, already built) — auto-generate thumbnails
- `LMS` (BEA repo) — auto-PR a new module
- `portal-uk` / `portal-us-ca` / `BEA_Creator_Portal` — embed in creator dashboard

**Design:** A `publish.py` step at the end of the pipeline that:

1. Calls `YouTube-Thumbnail` to render thumbnail
2. Uploads video (unlisted YouTube + R2 backup)
3. Opens a PR against `LMS` adding the module manifest
4. Posts a notification to the relevant portal's creator feed

---

## 5. Data flow walkthrough — a personalized example

**Trigger:** Sunday 6am cron, "weekly creator coaching video" job.

1. Job picks creator `@example`.
2. Toklytics API → last 30 days metrics + top 3 "Fixes" from latest report.
3. Orchestrator query to `mybrain`: "BEA guidance on [their top fix]?"
4. `mybrain` returns the relevant LIVE Guide sections + a similar creator's success story.
5. Orchestrator drafts outline: 90-sec video, 6 slides, personalized open.
6. Outline → `notebooklm-mcp-secure` (local mode for privacy) → returns deck + narration JSON.
7. `marketingskills` review pass: tightens CTAs, ensures "Issue/Why/Action" structure matches Toklytics report style.
8. `training-video-generator` renders MP4.
9. `YouTube-Thumbnail` renders thumbnail with creator handle.
10. Publishes to creator's portal feed (unlisted YouTube + R2).
11. Logs to a "watched / not-watched" tracking table for follow-up.

---

## 6. Phased rollout

### Phase 0 — Spike (1 week)

Goal: Prove `notebooklm-py` + `training-video-generator` can produce a watchable BEA-branded video end-to-end. No personalization. No automation. Manual orchestration.

**Deliverable:** One sample video on a fixed topic ("How to acknowledge a gifter") demoed internally.

**Decision gate:** Is the output quality acceptable as-is, or does video production need significant work before continuing?

---

### Phase 1 — MVP (3-4 weeks)

Goal: Self-serve generation from a topic + source URLs.

- [ ] Claude orchestrator wired up via Agent SDK
- [ ] `mybrain` ingesting BEA-Live-Guide + LMS + portal docs
- [ ] Prompt library curated from upstream collections
- [ ] `training-video-generator` BEA-branded (logo, fonts, colors)
- [ ] CLI: `bea-train generate --topic "..." --audience "..."`
- [ ] Output: MP4 + thumbnail + draft LMS module manifest

**Deliverable:** Team can generate any training video on demand.

---

### Phase 2 — Personalization (4-6 weeks)

Goal: Per-creator videos driven by Toklytics data.

- [ ] Toklytics integration (read-only API to pull creator metrics)
- [ ] Local-NotebookLM mode for personalized runs
- [ ] Personalization templates (creator name, their metrics, their fixes)
- [ ] Portal embed for creator-facing playback + completion tracking

**Deliverable:** Cron job producing weekly personalized videos for top N creators.

---

### Phase 3 — Scale (ongoing)

- [ ] A/B test prompts
- [ ] Multi-language (per region: UK, US/CA)
- [ ] Compliance auto-check via `marketingskills` + a "compliance review" agent
- [ ] Auto-update older videos when source docs change

---

## 7. Tech stack decisions (opinionated defaults)

| Layer | Choice | Rationale |
|---|---|---|
| Orchestration | TypeScript (Node) + Claude Agent SDK | Aligns with most of your existing portals |
| NotebookLM driver | Python (FastAPI service) | Forks are Python; cleanest path |
| Knowledge graph | `mybrain` defaults | Don't reinvent |
| Video gen | `training-video-generator` defaults + theme overlay | Defer customization |
| Storage | Cloudflare R2 | You already have Cloudflare account via MCP |
| Hosting | Cloudflare Workers (orchestrator) + a Railway/Fly worker (Python services) | Matches `bea-sob`'s pattern |
| Queue | Cloudflare Queues or Upstash | Async generation jobs |
| DB | Supabase (you have it in MCP) | Track generations, completions, A/B tests |

---

## 8. Repo layout (proposed)

```
bea-training-engine/
├── README.md
├── docs/
│   └── design.md  (this doc, migrated)
├── orchestrator/        # TS, Claude Agent SDK
│   ├── src/
│   └── package.json
├── notebooklm-service/  # Python, FastAPI
│   ├── src/
│   └── requirements.txt
├── video-service/       # Python, wraps training-video-generator
│   └── ...
├── prompts/             # curated prompt templates
│   ├── slide-outline.md
│   ├── narration.md
│   └── personalization.md
├── brand/               # BEA visual assets for video gen
│   ├── intro.mp4
│   ├── logo.png
│   └── theme.json
├── forks/               # git submodules
│   ├── mybrain/
│   ├── notebooklm-py/
│   ├── notebooklm-mcp-secure/
│   ├── training-video-generator/
│   └── ...
└── infra/               # Cloudflare + Supabase IaC
```

---

## 9. Risks & open questions

| Risk | Mitigation |
|---|---|
| Google NotebookLM ToS allows programmatic access? | Audit `notebooklm-py` README + upstream issues. Have `Local-NotebookLM` as fallback. |
| `training-video-generator` quality not agency-grade | Phase 0 spike answers this before further investment. |
| Per-creator personalization triggers TikTok ToS concerns | Personalization uses BEA's own data (Toklytics reports), not scraped TikTok data. Stay on-side. |
| Cost spirals at scale | Cap concurrent jobs; tier creators (top N get weekly, others monthly). |
| Forks drift from upstream | Submodule strategy with periodic sync; only vendor if we make significant local changes. |
| Skill registry sprawl (you have 6+ skill-related forks) | Pick ONE before starting. Recommend `marketingskills` + Anthropic's official `skills` repo as canonical. |

**Open questions:**

1. Do creators see this as "AI-generated training" or is it presented as BEA-branded content? (Honesty vs polish tradeoff.)
2. ~~Is per-creator personalization the v1 differentiator or a v2 unlock?~~ **Decided: V2 unlock.** Phase 1 MVP ships topic-driven generic training; Phase 2 layers in Toklytics-driven per-creator personalization.
3. Local vs cloud NotebookLM as default — privacy posture decision.
4. Who reviews/approves before publish, or is it fully auto?
5. Languages beyond English in scope for v1?

---

## 10. Concrete next steps

If we proceed:

1. Create the `bea-training-engine` repo under the BEA org.
2. Phase 0 spike: clone `training-video-generator` + `notebooklm-py`, manually orchestrate one BEA video. Time-box: 3 days.
3. Decision gate: review video with the team, decide on go/no-go for Phase 1.
4. If go: scaffold per layout in §8, set up Cloudflare + Supabase, start Phase 1 sprint.

---

## Appendix A — Fork inventory used

| Fork | Used in | Role |
|---|---|---|
| `mybrain` | §4.1 | Knowledge graph |
| `anthropic-sdk-typescript` | §4.2 | SDK |
| `claude-cookbooks` | §4.2 | Patterns reference |
| `marketingskills` | §4.2, §7 | CRO/copy skill |
| `notebooklm-skill` | §4.2 | Content planner skill |
| `notebooklm-mcp-secure` | §4.3 | MCP server |
| `notebooklm-py` | §4.3 | Python API |
| `Local-NotebookLM` | §4.3 | Local fallback |
| `awesome-notebookLM-prompts` | §4.3 | Prompt library |
| `notebooklm-prompts` | §4.3 | Prompt library |
| `training-video-generator` | §4.4 | Slides → MP4 |
| `YouTube-Thumbnail` (BEA-built) | §4.5 | Thumbnails |
| `LMS` (BEA-built) | §4.5 | Distribution target |

## Appendix B — Forks deliberately *not* used (and why)

| Fork | Why excluded |
|---|---|
| `agent-skills`, `agentskills`, `skills`, `agent-skillsnew`, `Agent-Skills-for-Context-Engineering`, `claude-plugins-official` | Pick one canonical skill source. Recommend keeping `marketingskills` (domain-specific) + upstream Anthropic `skills`. Archive the rest. |
| `electron`, `update.electronjs.org`, `darwinkit` | Not building desktop apps for this engine. |
| `bazelisk` | Overkill for this scope. |
| `faceswap` | Reputational risk. |
| `stripe-node` | Belongs in portals, not this engine. |
| `CloakBrowser`, `Scrapegraph-ai`, `reaper` | Belong in Toklytics / portal security work. |


<a id="2-quality-strategy"></a>

# 2. Quality Strategy

> Source: `docs/bea-training-engine-quality-strategy.md`

---

# BEA Training Engine — Quality Strategy

> The north-star **production quality** vision and the ladder that every spike, sprint, and decision must climb. Anchor doc — if a piece of work isn't moving us toward the end state defined here, it's the wrong work.
>
> **Companion doc:** `bea-training-engine-pedagogy.md` defines **content quality** (the teaching philosophy). Both must be satisfied for a module to ship. Production quality without pedagogy = a beautiful video that doesn't change behavior. Pedagogy without production quality = great training that creators won't watch. Both, or nothing.

---

## The end state, in one sentence

**Training videos that creators in BEA's TikTok LIVE network voluntarily watch to completion because they're as engaging as the YouTube content those creators already consume.**

That's the bar. Anything below it fails — not because the content is wrong, but because creators won't watch it long enough for the content to matter.

---

## Concrete quality benchmarks

The audience watches creators like MrBeast, Marques Brownlee, Patrick Boyle, Ali Abdaal, and countless TikTok creators all day. The training videos compete with that content for attention. Specific characteristics every BEA training video must hit:

| Dimension | Floor (must clear) | Aspiration (where we get to) |
|---|---|---|
| **First-5-seconds hook** | Specific scene a creator recognizes ("you just got a Lion, chat's exploding, what now?") | Hook that creators screenshot / share unprompted |
| **Voice** | Sounds natural enough that the AI-ness isn't distracting | Distinct BEA-brand voice creators recognize after 3 modules |
| **Visual pacing** | Visual change every 10-15 seconds | Visual change every 5-8 seconds; pattern interrupts feel like premium creator content |
| **Demonstrations** | At least one shown-not-told moment per module | Modules built around demonstrations; talking-head minimized |
| **Audio production** | Audible, no peaks, music bed present | Sound design — gift-pop SFX, transition stings, branded audio identity |
| **Captions / on-screen text** | Accurate SRT, readable size | Stylized kinetic typography matching brand |
| **Thumbnail** | Recognizably BEA, readable on mobile | Creators click without needing the title |
| **Retention curve** | ≥ 50% audience watch ratio at end | ≥ 75% audience watch ratio at end |
| **Per-video cost** | ≤ $5 fully automated | ≤ $3 fully automated |
| **Time from topic → published** | < 1 day end-to-end | < 1 hour end-to-end |

If a phase doesn't move us closer to the "aspiration" column, that phase is misaligned with the north star.

---

## Why this is non-negotiable

Three reasons:

1. **Audience reality.** Creators who can't sit through a polished MrBeast video won't sit through a plain training video. The audience has trained their attention on premium short-form content. Anything below that bar gets skipped — not because of content quality but because of production quality.

2. **Reputation transfer.** BEA's brand is "the agency that teaches creators to make exceptional content." If BEA's own training is mediocre, the agency's authority on quality content collapses. Bad training is reputational debt.

3. **Compounding effect.** Each plain training video that goes out lowers the perceived quality of every subsequent video. Re-establishing trust after shipping low-quality content costs more than building to quality from the start.

This is why "ship plain output and improve later" is a real risk — every plain video shipped erodes the audience's willingness to give the *next* video a chance.

---

## Quality dimensions, ranked by impact-per-effort

Where to invest first when raising the floor:

| # | Dimension | Effort | Quality lift | Cost |
|---|---|---|---|---|
| 1 | **Voice** (Kokoro → Google Cloud TTS Studio voices) | 1 day | Massive — biggest perceived-quality lever | ~$0.02/video |
| 2 | **Hook + structure** (prompt tuning for first-5-seconds rule) | 2 days | Large — affects retention curve directly | $0 |
| 3 | **Visual production system** (Remotion or similar templated renderer) | 3-4 wks | Large — moves output from "slideshow" to "video" | $0 (open source) |
| 4 | **B-roll / stock footage** (Pexels/Storyblocks API) | 1-2 wks | Medium-large — enables demonstrations | $0-1/video |
| 5 | **Music bed** (Epidemic Sound API) | 1 day | Medium — universal "premium" signal | ~$15/mo flat |
| 6 | **Thumbnail** (YouTube-Thumbnail tool's video_url mode) | Done, pending wire shape | Medium — affects click-through | $0-0.10/video |
| 7 | **Sound design** (transition stings, gift SFX) | 1 wk | Medium for top modules | $0 (own library) |
| 8 | **Kinetic typography** (animated captions/lower-thirds) | 1-2 wks | Medium | $0 |
| 9 | **Custom motion graphics** (animated diagrams) | Per-module work | High for specific modules | $0 if scripted in renderer |

The order matters. **Voice + structure + visual production** are 80% of perceived quality. Everything else is a polish layer.

---

## Phase ladder — each phase has an explicit quality gate

The pipeline doesn't ship to creators until each phase's gate is met. This is the discipline that prevents drift.

### Phase 0 — Logistics validation ⚠️ NOT for creator consumption

**Goal:** prove the pipeline assembles end-to-end.
**Quality target:** none. Plain output is acceptable here BECAUSE THE OUTPUT IS NOT SHIPPED.
**Gate:** can the engine produce + upload + add-to-playlist a video without manual intervention?
**Status:** ~complete.

This phase's job was to de-risk the integration. It is explicitly NOT producing content that creators will see.

---

### Phase 0.5 — Voice floor

**Goal:** raise voice quality to "not distracting".
**Specific work:**
- Switch `TTS_ENGINE` from `kokoro` to `gcloud` in `.env` — Google Cloud TTS Studio voices are already wired in. **No new vendor needed.** BEA is already on GCP via NotebookLM Enterprise, so same auth + billing.
- Lock a flagship voice per language and stick with it across all modules so it becomes "the BEA voice" by repetition:
    - English: `en-US-Studio-Q` (male, conversational) or `en-US-Studio-O` (female, natural) — pick one and own it
    - Spanish: `es-US-Studio-B`
- Tune narration prompt for natural conversational cadence (not slide-readout style)

**Gate:** play a generated video for a creator-volunteer (someone in the BEA network, not the team). They cannot tell within 30 seconds that the voice is AI-generated, OR they can tell and don't care because the content is engaging.

**Why this phase before the bigger Phase 1:** voice is the single biggest perceived-quality lever and it's a configuration change + a 1-day prompt tuning pass. Hitting Phase 0.5's gate validates that the *content* generation is good enough that voice was the bottleneck. If creators reject even with a good voice, the problem is content / structure / pacing — and that's a different fix than visual production.

**Cost impact:** ~$0.02 per 90-second video at Studio voice rates (versus ~$0 for Kokoro). Negligible at any reasonable volume.

**Status:** not started. Trivially small unblock — flip the env var, validate.

**ElevenLabs note:** explicitly NOT recommended. The only thing it offers over Google Cloud Studio voices is *voice cloning* (e.g., cloning a BEA team member's voice as the brand voice). For now, picking a consistent Studio voice and using it across all modules accomplishes the same brand-recognition goal without adding a vendor or cost. Revisit cloning only if creator-volunteer testing comes back with "voice quality is fine but feels generic" feedback — that's a Phase 1 follow-on, not a launch dependency.

---

### Phase 1 — Visual production floor

**Goal:** move from slideshow to actual video. **Architecture:** see `bea-training-engine-remotion-architecture.md` for the full spec.
**Specific work:**
- Replace PIL slide renderer with **Remotion** (React/TS, fits the Vercel + Next stack already in BEA's footprint)
- Build one React component per pedagogy slide kind (`<Hook />`, `<What />`, `<Why />`, `<How />`, `<Script />`, `<Mistake />`, `<Success />`, `<Recap />`, `<Identity />`, `<Action />`, `<Reflection />`, `<Checkpoint />`) — this is how the pedagogy is enforced in the type system
- Wire stock b-roll API (Pexels free for Sprint 3; revisit Storyblocks later) — Claude includes search queries per scene
- Add music bed with auto-ducking under narration
- Brand token system in `theme/tokens.ts` so updating colors / fonts updates every video

**Gate:** show a generated video to a creator-volunteer alongside a real BEA-team-produced video. They cannot pick out the AI-generated one based on production quality. (Content tone may differ; production quality should not.)

**Output target:** retention curve ≥ 50% audience watch ratio at end; 90% would-watch-again rating from 5 creator-volunteers.

**Why this phase is the big one:** this is where the engine becomes shippable. Phase 0 + 0.5 are preparation; Phase 1 is the actual product.

**Status:** not started. The Remotion piece is the only large unknown.

---

### Phase 2 — Personalization + multilingual + analytics-driven improvement

**Goal:** every creator gets training tuned to their actual Toklytics data, in their language, that gets better over time.
**Specific work:**
- Pull per-creator Toklytics insights as additional context for Claude
- Spanish (es-US) variant pipeline already built — validate it ships at Phase 1 quality
- Wire YouTube Analytics drop-off-slide detection into a prompt-tuning loop
- A/B test prompt template variants
- Module versioning + re-render when source docs update

**Gate:** per-creator videos hit the same Phase 1 retention bar AND show measurable behavior change in Toklytics metrics for ≥ 30% of creators who complete a module.

**Status:** scaffolding exists (translator, analytics_collector); Phase 1 is the prerequisite.

---

### Phase 3 — Premium tier workflow

**Goal:** flagship modules that compete with top-tier creator-academy content (e.g., Patreon-quality, Skillshare-quality).
**Specific work:**
- Two-tier production model: Standard (engine) + Premium (engine generates script + storyboard, human producer assembles)
- Real footage from BEA's top creators (with permissions)
- Custom motion graphics per flagship module
- Higher voice tier (real voiceover artist, or hand-tuned ElevenLabs per module)

**Gate:** flagship modules are indistinguishable from a $1000-budget produced training video on YouTube. Marketing-grade.

**Output target:** flagship modules can be promoted on the BEA YouTube channel as public content (changing the unlisted-only policy for these specifically), serving as agency marketing collateral.

**Status:** scoped but not specified in detail. Roughly $200-1000 per flagship video in human time + tooling.

---

## How phases interact with the existing spike kit

Most of what's already built lives across Phase 0 + 0.5 + 1:

| Component | Phase that defines its quality bar |
|---|---|
| `notebooklm_client.py`, `slide_deriver.py` | Phase 0 (logistics) — content quality refined Phase 0.5+ via prompt tuning |
| `tts_client.py` | Phase 0.5 — swap engines, keep interface |
| `video_renderer.py` (PIL) | Phase 0 only — Phase 1 replaces with Remotion |
| `captions_generator.py` | Phase 1 — basic SRT works now; kinetic typography is a Phase 1 polish |
| `thumbnail_generator.py` | Phase 1 — three backends exist; choose Gemini-driven for production |
| `youtube_publisher.py` | All phases — unchanged |
| `translator.py` | Phase 2 — already built |
| `analytics_collector.py` | Phase 2 — drop-off-slide detection feeds the prompt-tuning loop |
| `module_status.py` (editorial workflow) | All phases — review bar gets stricter as quality bar rises |

The architecture supports the upgrade path. We don't have to throw work away to climb the ladder.

---

## Anti-patterns to actively avoid

1. **Shipping plain output to creators "just to see what happens"** — every plain video erodes audience trust. The gates are there to prevent this.
2. **Treating Phase 0 output as evidence the engine works** — Phase 0 proves logistics, not product readiness. Don't conflate.
3. **Bypassing the editorial review gate to ship faster** — review is part of how quality is enforced. The trust ladder (Phase 2 per-batch approval) exists for after the team has earned it, not before.
4. **Investing in tier 3 polish (sound design, kinetic typography) before tier 1 floor (voice, visuals)** — the polish layers don't compound on a broken foundation.
5. **Building the premium tier inside the same engine** — keep it separate. The engine is for high-volume standard training. Premium content sits beside it.
6. **Locking in a SaaS video-gen vendor (Synthesia, HeyGen)** — those produce a recognizable visual style. Once seen, can't be unseen. BEA's brand can't look like every other Synthesia-produced training video.

---

## Decision principles

When a tradeoff comes up during a sprint, default to these:

- **Voice quality > content variety.** One excellent module > ten plain modules.
- **Demonstrations > explanations.** Always cut a slide that just describes a concept; replace with a slide that shows it.
- **Brand-consistent visual style > AI variety.** Templated production beats AI-generated visuals when AI variety hurts brand consistency.
- **Retention beats reach.** Unlisted videos with 75% retention beat public videos with 30% retention for an agency-training use case.
- **Re-render before "improve in post."** If a video falls short of the bar, regenerate from the engine, don't manually patch.

---

## Definition of done — for the engine, not for any one phase

The engine is "done" (and the BEA Training Engine project graduates) when:

1. 50+ standard training modules have shipped through it
2. Median module retention curve ≥ 75% audience watch ratio at end
3. ≥ 10% of completed modules trigger measurable creator behavior change in Toklytics metrics
4. Per-module cost ≤ $3 fully automated
5. New module from topic → published takes ≤ 1 hour
6. A flagship Premium module produced via the two-tier model is publishable on @boldevolution publicly as marketing collateral

Until those six conditions are met, the project is in flight. Phase 0's plain output is *step 1 of a long climb*, not the destination.

---

## Open strategic choices to make soon

1. ~~**Voice provider:** ElevenLabs vs real human VO vs hybrid~~ **Resolved:** Google Cloud TTS Studio voices (already in stack via GCP). Real human VO reserved for Premium-tier (Phase 3) flagship modules.
2. ~~**Visual framework:** Remotion vs Manim vs SaaS?~~ **Resolved:** Remotion. Architecture in `bea-training-engine-remotion-architecture.md`.
3. **Stock footage budget:** Pexels free (likely enough for most modules), Storyblocks ~$30/mo (better catalog), or Artgrid ~$300/yr per seat (premium)?
4. ~~**Brand voice consistency:** clone or pro voice?~~ **Resolved:** lock a consistent Google Cloud Studio voice per language (`en-US-Studio-Q` or `en-US-Studio-O` for English, `es-US-Studio-B` for Spanish). Revisit cloning only if creator-volunteer testing demands a more memorable voice.
5. **Flagship cadence:** how many Premium-tier modules per quarter? Drives the human-producer budget for Phase 3.

These don't need answers today but should be answered before Phase 0.5 starts.


<a id="3-pedagogy"></a>

# 3. Pedagogy

> Source: `docs/bea-training-engine-pedagogy.md`

---

# BEA Training Engine — Pedagogy

> The teaching philosophy every BEA training module must follow. This is the *content quality* equivalent of `bea-training-engine-quality-strategy.md` (production quality). Both must be satisfied for a module to ship.
>
> Every prompt template, every Remotion scene, every editorial review checklist references this doc. If a module breaks these rules, it's rejected — regardless of how good the production is.

---

## Mission

The training engine is NOT an explainer. It is a **behavioral training system** for TikTok LIVE creators. Its purpose is to:

- Increase creator execution
- Improve retention of information
- Improve behavioral consistency
- Increase LIVE performance
- Reduce overwhelm
- Increase confidence through clarity
- Create repeatable action patterns
- Improve habit formation
- Drive measurable creator outcomes

If a module doesn't move at least one of these levers for the watching creator, it's the wrong module.

---

## The strategic positioning

**BEA's biggest advantage is NOT the information.** Information about TikTok LIVE is widely available. Anyone can find it.

What's rare is training that is **behaviorally engineered**. Specifically:

- **Structure** — every lesson follows the same shape so creators always know where they are
- **Reinforcement** — recap, retrieval, spaced repetition across modules
- **Personalization** — content tuned to the creator's actual Toklytics data (Phase 2)
- **Actionability** — every lesson ends in a specific immediate behavior
- **Emotional relevance** — outcomes tied to what creators actually care about
- **Consistency systems** — habit triggers, checkpoints, identity reinforcement

Most creator education online is informational. Very little is behaviorally engineered. **That's the actual moat.** The engine has to deliver on this, not just produce videos.

### Research bases

This approach draws from established learning science. Module design references these directly:

- **Cognitive Load Theory** (Sweller) — chunking, dual coding, minimal extraneous load
- **Self-Determination Theory** (Deci & Ryan) — autonomy, competence, relatedness as motivators
- **Social Learning Theory** (Bandura) — modeling via creator examples, identity-based reinforcement
- **Spaced Repetition** — concepts repeated across modules with increasing intervals
- **Retrieval Practice** — recap questions force active retrieval, not passive review
- **Dual Coding Theory** (Paivio) — visual + verbal channels in every scene
- **Andragogy** (Knowles) — adult learners need relevance, problem-centered framing, and immediate application

---

## Audience profile (designed-for)

- Adults 18–50
- Mixed educational backgrounds
- Often low attention span — social-media conditioned, mobile-first
- Emotionally-driven learners
- ADHD-friendly formatting required
- Many are overwhelmed or inconsistent
- Many learn by doing, not by theory

Every formatting decision, every word choice, every visual is for this learner. Not "general adult learners." Not "online students." **This specific audience.**

---

## The 14 rules every module follows

### 1. Teach only actionable concepts
- Skip unnecessary theory. Explain only what helps execution.

### 2. Reduce cognitive load
- Short sections. One core idea at a time. No walls of text. No jargon unless immediately explained.

### 3. Use microlearning structure
- Short lessons. Clear outcomes. Immediate application.

### 4. Use retrieval reinforcement
- Recap questions, "what should you do next?" checks, repeat key concepts in different wording.

### 5. Use behavior-driven framing
- Explain WHY emotionally + practically. Connect actions to outcomes creators care about: **money, growth, visibility, audience loyalty, confidence, consistency.**

### 6. Use identity-based reinforcement
- Reinforce the professional creator identity. Frame consistency as part of who they are, not a chore.

### 7. Use dual coding principles
- Whenever possible: visuals, examples, scripts, templates, diagrams, checklists.

### 8. Use pattern interruption
- Vary formatting. Bullets, examples, comparisons, scenarios.

### 9. Prioritize implementation — answer 5 questions per lesson
1. **What is this?**
2. **Why does it matter?**
3. **What do I do?**
4. **What does success look like?**
5. **What mistakes should I avoid?**

### 10. Close every lesson with three things
- **1 immediate action** the creator does right now
- **1 reflection question**
- **1 measurable checkpoint** (track this over N days)

### 11. Optimize for mobile consumption
- Short paragraphs. Scannable. Clear headings.

### 12. Avoid
- Corporate tone, academic writing, vague motivation, filler, generic inspiration, information dumping.

### 13. Tone
- Intelligent. Direct. Practical. Supportive without being fake. Performance-oriented. Clear and structured.

### 14. Priorities
- Execution over inspiration.
- Clarity over complexity.
- Repetition over novelty.
- Systems over hype.

---

## The 10-section lesson structure (macro)

Every lesson follows this exact section flow. Creators learn the rhythm and always know where they are in a module. Structure = trust.

| # | Section | What it does |
|---|---|---|
| 1 | **Why This Matters** | Tie the topic to an outcome the creator cares about. Open the emotional loop. |
| 2 | **The Core Principle** | One-sentence definition of the concept. The big idea. |
| 3 | **What This Looks Like On LIVE** | Concrete example — a creator scenario unfolding. Show, don't just tell. |
| 4 | **How To Apply It** | Step-by-step actions. The procedural core. |
| 5 | **Common Mistakes** | Failure patterns with their corrections. |
| 6 | **Pro Tip** | Advanced insight that elevates basic application. |
| 7 | **Quick Win Challenge** | A small immediate action — done on the next LIVE. |
| 8 | **Reflection Question** | Forces active thinking. Open question. |
| 9 | **Success Checkpoint** | Measurable metric the creator tracks over N LIVEs. |
| 10 | (optional — for long modules) **Recap** | Retrieval-practice question forcing them to reconstruct what they just learned. |

The first three sections (Why → What → Example) open the loop and create relevance. The middle three (How → Mistakes → Pro Tip) deliver the actionable substance. The last three (Quick Win → Reflection → Checkpoint) drive behavior change.

Title precedes section 1 as a standalone hook scene.

---

## Typed slide vocabulary (micro — scenes within sections)

Every slide has a `kind` field. There is no generic slide. Each section is one or more typed scenes:

| `kind` | Section it lives in | Purpose | Constraint |
|---|---|---|---|
| `hook` | (pre-section 1) | First 3-5s. Specific recognizable scene from a LIVE. No "welcome." | Exactly 1 per module, always slide 1 |
| `why` | Why This Matters | Emotional + practical reason this matters | Always references money/growth/visibility/loyalty/confidence/consistency |
| `what` | The Core Principle | One-sentence concept definition | Usually 1 slide |
| `live_example` | What This Looks Like On LIVE | Concrete scene of a creator applying (or failing at) the concept | Vivid, specific, names a moment |
| `how` | How To Apply It | Numbered step-by-step action | 2-4 steps max; if more, split the module |
| `script` | How To Apply It (or standalone) | Exact words/phrases to use during LIVE | Always a fillable template with `[brackets]` |
| `mistake` | Common Mistakes | Common failure pattern + correct alternative | Names the specific wrong behavior |
| `pro_tip` | Pro Tip | Advanced insight beyond the basic application | One insight only; don't dilute |
| `action` | Quick Win Challenge | "Do this immediately" — specific, time-bound | Always references next LIVE |
| `reflection` | Reflection Question | Open question creator sits with | Personal, emotional, single sentence |
| `checkpoint` | Success Checkpoint | Measurable target over N days/LIVEs | Always quantified with a number |
| `success` | (insertable anywhere) | What "doing it right" looks like with a metric | Optional pattern interrupt |
| `recap` | (optional, end of long modules) | Retrieval-practice question | Open question, never yes/no |
| `identity` | (insertable, sparingly) | One line reinforcing professional creator identity | Max 1 per module |

A 90-second module: 9-11 slides (one per section, plus hook). A 3-minute module: 16-20 slides (some sections expand to 2-3 slides). The closing trio (`action` / `reflection` / `checkpoint`) is non-optional.

---

## Psychology Mode — pre-generation analysis

**Before generating any module, the engine analyzes the learner first.** This is a meta-step that prevents generic AI output. Output is a `psychology_analysis` object that becomes input to the slide generation pass.

The analysis answers:

1. **Motivational drivers** — what specifically motivates a creator to act on this topic? (Money? Visibility? Audience loyalty? Confidence?)
2. **Likely attention failures** — what will make them swipe away? (Too theoretical? Slow open? Familiar info?)
3. **Likely emotional resistance** — what beliefs / fears resist this lesson? ("This won't work for my niche", "I tried this before and it failed", "This feels fake")
4. **Likely execution barriers** — what stops them from doing the thing? (Time? Equipment? Confidence? Awareness?)
5. **Adaptation strategy** — given the above, what specific tactical choices does the module make?

The slide generation pass then references this analysis. If the audience's biggest barrier is "feels fake when I try it," the `mistake` slide directly addresses the fake-feeling concern. If the biggest motivator is money, the `why` slide leads with the gift-revenue tie. The analysis tunes the module to the actual psychology, not a generic creator.

This step is non-optional. Every module generated has a stored psychology analysis as a sibling file (`psychology.json`). Editorial review can audit whether the module actually addresses the analyzed barriers.

---

## Social-media-specific psychology to weave in (when relevant)

Modules touching audience behavior reference these levers explicitly:

- **Audience retention** — what makes a viewer stay vs swipe
- **Reward loops** — what triggers gift / comment / follow
- **Emotional pacing** — high/low intensity rhythm
- **Attention resets** — visual/audio interrupts that re-engage
- **Viewer fatigue** — signs your audience is tuning out
- **Parasocial behavior** — the relationship creator-to-viewer
- **Consistency signaling** — how showing up reliably builds trust
- **Perceived authority** — micro-cues that establish credibility
- **Trust formation** — the timeline and behaviors that build it

These aren't theoretical asides — they're framing for *why* a specific tactic works.

---

## How the engine enforces this

| Layer | Enforcement |
|---|---|
| **Prompt templates** (`prompts/slide-outline.md`, `prompts/narration.md`) | Hard-coded structure that produces typed slides per §"How a module is structured." Tone rules baked in. |
| **Claude slide-deriver** | Validates output JSON against the typed-slide schema before saving. Bad outputs get re-prompted, not patched. |
| **Remotion templates** | One React component per slide `kind`. There's no "generic slide" component, so off-pattern slides literally cannot render. |
| **Editorial review** | Checklist includes pedagogy compliance (closing trio present, 5-question structure satisfied, tone passes vibe check). |
| **Analytics feedback** | Drop-off-slide detection (from `analytics_collector.py`) feeds back into prompt-tuning when specific slide kinds consistently underperform. |

The system has multiple enforcement layers because content quality drift is the highest risk in any AI-content pipeline. One enforcement layer is not enough.

---

## What this is NOT

- **Not a stylistic preference.** These rules are the product. A module that produces a good-looking video but violates rule 9 or 10 is a defective product.
- **Not optional for "simple" modules.** Even a 60-second module on "acknowledging gifters" has a hook + what + why + how + action + checkpoint. Just shorter.
- **Not a creative ceiling.** Within these rules, every module should feel different — different hooks, different examples, different scripts. Repetition of *structure*, novelty of *content*.
- **Not aspirational.** This is the bar at launch. Phase 0.5 modules that don't follow this pedagogy are not promoted to creators, full stop.

---

## What "good" looks like in practice

A 90-second module on "Acknowledging gifters within 8 seconds" — laid out by the 10-section structure with the typed slide kinds underneath:

| Time | Section | Slide kind | What's on screen + spoken |
|---|---|---|---|
| 0:00-0:05 | (Hook) | `hook` | A Lion just dropped in your LIVE. Chat is exploding. You have 8 seconds. |
| 0:05-0:18 | Why This Matters | `why` | Top creators who acknowledge in <8s see 3x higher repeat-gift rate. The gifter has to feel seen — that's the entire emotional contract of a LIVE. |
| 0:18-0:26 | The Core Principle | `what` | "Acknowledge fast" = name the gifter + name the gift within 8 seconds of landing. |
| 0:26-0:38 | What This Looks Like On LIVE | `live_example` | Mid-rant about your day. Sarah drops a Lion. You stop mid-sentence: "Sarah — that Lion. You just made tonight." Chat lights up. Three more gifts in the next 20 seconds. |
| 0:38-0:55 | How To Apply It | `how` | Three steps: (1) stop your sentence mid-word. (2) say their @handle + gift name. (3) one specific thank-you, not generic. |
| 0:55-1:05 | How To Apply It | `script` | "Yo [@username] — that [Lion]. Thank you. You just made tonight." |
| 1:05-1:15 | Common Mistakes | `mistake` | Don't say "thanks for the gifts" when ONE specific person dropped it. They tune out. Name them. |
| 1:15-1:23 | Pro Tip | `pro_tip` | If you forget the gift's name, just say "that gift" — speed beats precision. The 8-second window matters more than getting the name right. |
| 1:23-1:32 | Quick Win Challenge | `action` | On your next LIVE: the second a top gift lands, start a mental 8-second timer. Force yourself to name + thank before it runs out. |
| 1:32-1:40 | Reflection Question | `reflection` | Which gifters made YOU feel seen last week? What did they say? |
| 1:40-1:50 | Success Checkpoint | `checkpoint` | Track this for 7 LIVEs: how often did you acknowledge within 8 seconds? Aim for 80%. |

That's the standard. Every module hits that structure or doesn't ship.

---

## Where this doc gets consumed

- `prompts/slide-outline.md` — references this doc by name and inherits the structure
- `prompts/narration.md` — references this doc for tone + closing-trio rules
- `docs/bea-training-engine-remotion-architecture.md` — typed-slide vocabulary maps 1:1 to Remotion components
- `bea-training-engine-spike/src/module_status.py` — editorial review checklist includes pedagogy compliance items
- `docs/bea-training-engine-quality-strategy.md` — references this doc as content-quality bar (alongside the production-quality bar)

If you change something here, all of the above need to track the change.


<a id="4-remotion-architecture"></a>

# 4. Remotion Architecture

> Source: `docs/bea-training-engine-remotion-architecture.md`

---

# BEA Training Engine — Remotion Architecture

> Production-quality video assembly for Phase 1, replacing the Phase 0 PIL slideshow renderer.
>
> **Prerequisite reading:** `bea-training-engine-pedagogy.md` (every Remotion component maps to a typed slide kind defined there) and `bea-training-engine-quality-strategy.md` (this implements Phase 1's "visual production floor").

---

## Why Remotion

| Option considered | Why Remotion wins |
|---|---|
| PIL slideshow (Phase 0) | Plain. Static. Disqualifies on production quality. |
| Manim (Python) | Math-focused. Wrong primitives for creator training. |
| After Effects automation | Adobe tax, no version control, fragile macros. |
| Pictory / SaaS video gen | Recognizable SaaS style — every Pictory video looks like every other. Brand can't differentiate. |
| **Remotion** | React/TypeScript → fits Vercel + Next.js stack BEA already runs. Programmatic = version controlled. Open source = no vendor. Output is real broadcast-quality video. |

Remotion renders React components to MP4 via Chrome + ffmpeg. Each slide kind becomes one component. The deck.json from Claude drives composition.

---

## Architecture

```
deck.json (with typed slides per pedagogy)
    ↓
Remotion project (apps/video-renderer)
    ├── compositions/
    │   └── TrainingModule.tsx     ← top-level <Composition>, reads deck.json
    ├── scenes/                    ← one component per slide kind (14)
    │   ├── Hook.tsx
    │   ├── Why.tsx
    │   ├── What.tsx
    │   ├── LiveExample.tsx        ← NEW: visualizes "What This Looks Like On LIVE"
    │   ├── How.tsx
    │   ├── Script.tsx
    │   ├── Mistake.tsx
    │   ├── ProTip.tsx             ← NEW: visualizes "Pro Tip" section
    │   ├── Success.tsx
    │   ├── Recap.tsx
    │   ├── Identity.tsx
    │   ├── Action.tsx
    │   ├── Reflection.tsx
    │   └── Checkpoint.tsx
    ├── sections/                  ← optional section-divider transitions
    │   └── SectionTitle.tsx       ← "Why This Matters" / "How To Apply It" etc. cards
    ├── elements/                  ← reusable building blocks
    │   ├── BrandIntro.tsx         ← 2-second branded open
    │   ├── BrandOutro.tsx
    │   ├── LowerThird.tsx
    │   ├── ProgressBar.tsx
    │   ├── KineticText.tsx        ← animated text reveals
    │   ├── BackgroundLayer.tsx    ← brand-color gradient / motion bg
    │   └── BRollPlayer.tsx        ← stock footage embed
    ├── audio/                     ← narration + music bed
    ├── theme/                     ← brand tokens
    │   └── tokens.ts
    └── remotion.config.ts
    ↓
npx remotion render TrainingModule out/video.mp4 \
    --props='{"deckPath": "outputs/01-deck-spike/deck.json"}'
    ↓
The same .mp4 the existing publisher / captions / playlist hand-off consumes.
```

Remotion is invoked from the Python orchestrator via subprocess. The boundary stays clean: Python handles NotebookLM + Claude + YouTube; TypeScript/React handles visuals.

---

## Component contract per slide `kind`

Each scene component receives a `slide` prop matching the deck.json shape. Each component renders for `slide.estimated_seconds` and is responsible for its own animation timing.

### `<Hook />`

**Visual:** Full-bleed background (motion gradient or contextual b-roll), large kinetic title text appears word-by-word, subtitle line beneath. No logo (don't break the moment).

**Animation:** Snap-zoom into the scene at t=0. Title types/reveals during the first 1.5s. Background subtly drifts.

**Reference look:** the cold open of a MrBeast video — visual + audio commitment in the first 2 seconds. No room for "welcome."

### `<What />`

**Visual:** Center-screen card with the one-line definition. Subtle accent bar on the left edge (brand color). Logo top-left.

**Animation:** Card slides up + fades in at t=0. Definition text reveals at ~1 word per 200ms. Hold static for the rest of the slide.

### `<Why />`

**Visual:** Two-column split. Left: the "feeling" (emotional). Right: the metric/outcome (practical). Background tint shifts to a warmer brand color signaling "stakes."

**Animation:** Left column reveals first; right column reveals on the second beat for contrast.

### `<LiveExample />`

**Visual:** Cinematic frame styled like a TikTok LIVE viewport — vertical phone outline, mock chat scrolling on the side, gift drops animated in. The narration is a scene unfolding ("Sarah drops a Lion. You stop mid-sentence…"); the visual mirrors what the narrator describes.

**Animation:** Scene plays out — chat scrolls, gift appears, creator's caption text types out. This is the most cinematic scene kind. Heavier b-roll opportunity.

### `<ProTip />`

**Visual:** Confidential-feeling card — slightly different background (darker, with a subtle "advanced creator" badge or accent), single insight in bold type, small leverage-indicator (e.g., "↑ 2x retention" or "↓ 50% prep time") if applicable.

**Animation:** Slow zoom-in on the card. Insight reveals all at once, not word-by-word — feels deliberate, not flashy. This is the "I'm telling you something only the top creators know" beat; restraint sells it.

### `<How />`

**Visual:** Numbered step list (max 4). Each step is its own animated row with a number circle, step text, and an icon.

**Animation:** Steps reveal sequentially — step 1 lands at t=0, step 2 at ~3s, step 3 at ~6s. Narration is timed to match. The step the narrator is currently on is highlighted; others dim.

### `<Script />`

**Visual:** Quote-card design — the fillable template appears like a chat bubble. `[bracketed]` parts are visually distinct (different color, lighter weight) to signal "fill in".

**Animation:** Bubble appears, then the brackets briefly pulse to draw attention. The narrator demonstrates by example.

### `<Mistake />`

**Visual:** Pattern-interrupt — different background color (red-tinted), explicit "DON'T → DO" structure. Strikethrough on the DON'T text. Big arrow or transformation visual.

**Animation:** DON'T appears first, gets struck through. DO appears underneath with a green accent. This visual contrast is the whole point.

### `<Success />`

**Visual:** Large metric front-and-center. Surrounding context smaller. Brand accent color in confident green or gold.

**Animation:** Metric counts up to its final value over ~1.5s (e.g., "0 → 80%"). This is a small dopamine hit for the viewer.

### `<Recap />`

**Visual:** Center-screen question, large type. Visual cue that this is a pause moment — maybe a "?" character with subtle pulse, or a progress dot animation.

**Animation:** Question reveals slowly. Hold for a beat after narration finishes — give the creator a real second to think before the next slide.

### `<Identity />`

**Visual:** Minimal. Quiet card with a statement. Almost no animation. Lets the moment breathe.

**Animation:** Slow fade-in. Hold. Slow fade-out.

### `<Action />`

**Visual:** High-energy. Call-to-action card. Big arrow or pointing-forward visual. "DO THIS:" prefix.

**Animation:** Snap-cut entry. Text reveals fast. Brand accent color at maximum intensity.

### `<Reflection />`

**Visual:** Slow, intimate. Single question centered. Soft background. No movement other than slight drift.

**Animation:** Slowest pacing in the module. Question lingers.

### `<Checkpoint />`

**Visual:** Tracker-style card with the metric and duration. Looks like something the creator could screenshot and save (and is encouraged to).

**Animation:** Card lifts in. Metric number animates in last. Subtle "save this" cue at the bottom — could literally show a screenshot icon.

---

## Brand token system

Every component reads from `theme/tokens.ts`:

```typescript
export const brand = {
  name: "Bold Evolution Agency",
  channel: "@boldevolution",
  colors: {
    primary: "#000000",          // PLACEHOLDER — replace with real BEA colors
    secondary: "#FFFFFF",
    accent: "#000000",
    background: "#FAFAFA",
    danger: "#E63946",           // for <Mistake />
    success: "#06A77D",          // for <Success />
    emphasis: "#F4A261",         // for highlights
  },
  fonts: {
    heading: "Inter",
    body: "Inter",
    mono: "JetBrains Mono",
  },
  motion: {
    fastFrames: 9,               // ~0.3s at 30fps
    mediumFrames: 24,            // ~0.8s
    slowFrames: 45,              // ~1.5s
  },
  logo: staticFile("logo.png"),
  introClip: staticFile("intro.mp4"),
  outroClip: staticFile("outro.mp4"),
  musicBed: staticFile("music-bed.mp3"),
};
```

Updating brand values updates every video. No per-scene magic numbers.

---

## Audio handling

The Python orchestrator already produces:

- Per-slide narration audio (Kokoro or Google Cloud TTS Studio)
- `timing.json` recording each slide's start / end / duration

Remotion consumes:

- Pre-rendered narration MP3/WAV from the orchestrator (passed in as a static file)
- Optional music bed from `theme/tokens.ts`
- Optional per-scene SFX (gift-drop sound for `<Hook />`, "ding" for `<Recap />`, etc.)

The `<Audio>` component in Remotion handles mixing. The music bed auto-ducks under narration by reducing its volume during narration segments (using the `timing.json` to know when).

This means the existing Python TTS pipeline doesn't need to change. Remotion is a renderer, not a re-orchestrator.

---

## Stock footage / b-roll integration

For `<How />`, `<Mistake />`, `<Success />` scenes that benefit from b-roll, the deck.json can optionally specify search queries Claude picked:

```json
{
  "kind": "how",
  "title": "Three steps",
  "narration": "...",
  "broll_query": "person on phone in cozy room",
  "broll_orientation": "vertical"
}
```

A `BRollPlayer` element calls the Pexels (or Storyblocks) API at render time, downloads a clip, and uses it as a background under the text. Falls back to brand gradient if no clip matches.

**This is opt-in per slide.** Not every scene needs b-roll — over-using it creates visual chaos. Start with: `<Hook />` always has b-roll, `<How />` sometimes has it, `<Mistake />` rarely. Tune over time.

---

## Build plan — Phase 1 sprints

### Sprint 1 (1 week) — skeleton + 3 components
- Spin up Remotion project at `bea-training-engine-spike/remotion/`
- Wire the orchestrator to invoke `npx remotion render` from Python
- Build `<Hook />`, `<What />`, `<How />` first — these are the most-used and define the visual language
- Render a test module end-to-end with these 3 kinds; fall back to a generic card for the others
- **Gate:** the test module looks demonstrably better than the Phase 0 PIL output

### Sprint 2 (1.5 weeks) — remaining components
- Build `<Why />`, `<LiveExample />`, `<Script />`, `<Mistake />`, `<ProTip />`, `<Success />`, `<Recap />`, `<Identity />`, `<Action />`, `<Reflection />`, `<Checkpoint />`
- Build `<SectionTitle />` divider for the 10 lesson sections (optional but useful for longer modules)
- Polish brand tokens with the real BEA visual identity (replace placeholder colors)
- Add intro/outro brand stings
- **Gate:** generate the "Acknowledging gifters within 8 seconds" example module end-to-end with all 13 slide kinds rendering correctly (per the pedagogy doc's worked example)

### Sprint 3 (1 week) — b-roll + music + polish
- Pexels API integration for `<Hook />` and selected `<How />` scenes
- Music bed with auto-ducking
- Kinetic typography polish
- Per-scene timing tweaks based on creator-volunteer feedback
- **Gate:** creator-volunteer blind test passes — they cannot pick the AI-generated video from a team-produced one on production quality

### Sprint 4 (buffer) — feedback iteration
- A/B test 2-3 visual variants
- Tune based on Phase 1.5 analytics (drop-off-slide data from YouTube)

Total: ~3-4 weeks to Phase 1 "visual production floor" cleared.

---

## What stays Python, what becomes TypeScript

| Stays Python | Becomes TypeScript |
|---|---|
| NotebookLM Enterprise client | — |
| Claude slide derivation | — |
| TTS (Kokoro / GCP) | — |
| Translation | — |
| Captions generator (SRT) | — |
| YouTube publisher | — |
| Analytics collector | — |
| Editorial workflow state machine | — |
| `video_renderer.py` (PIL) | **Replaced by Remotion** |
| Orchestrator | Spawns Remotion as a subprocess; orchestrator stays Python |

The TypeScript surface is small and bounded. ~15 React components + a few utility modules. No state management, no API layer, no auth. Just a video renderer.

---

## Where the orchestrator changes

`spike_orchestrator.py render-video` currently calls `VideoRenderer` (PIL). Phase 1 swaps this to:

```python
subprocess.run(
    [
        "npx", "remotion", "render",
        "remotion/src/index.ts",  # entry point
        "TrainingModule",          # composition ID
        str(output_path),          # output MP4
        f"--props={json.dumps({
            'deckPath': str(deck_path),
            'narrationDir': str(narration_dir),
            'timingPath': str(timing_path),
            'brand': brand_dict,
        })}",
    ],
    check=True,
    cwd="remotion/",
)
```

Everything downstream (captions, publish, etc.) consumes the same MP4 + timing.json files. The orchestrator's CLI doesn't change.

---

## Risk register

| Risk | Mitigation |
|---|---|
| Remotion render times exceed practical limits at scale | Render takes ~1-2× video length on a modern machine; cloud Remotion (Remotion Cloud or self-hosted Lambda) caches for high volume |
| TypeScript adds a new toolchain to maintain | Bounded — no API, no state mgmt. Pin to a Remotion version and lock dependencies. |
| Visual style ends up feeling "templated" | Each scene component has 2-3 visual variants picked at random per slide. Pattern repetition becomes signature, not boredom. |
| Brand design tokens are wrong at launch | Sprint 1 ships with placeholders; Sprint 2 swaps in real brand values once the designer has them ready. |
| Stock footage doesn't match the topic well | Curate a vetted starter library locally; Pexels fallback is only for novel topics. |

---

## Why this aligns with the pedagogy

The pedagogy doc defines typed slide kinds. Remotion's component-per-kind architecture means **the system literally cannot render an off-pattern slide.** If Claude produces a slide without a `kind`, the Remotion composition errors out. If a `kind` is invalid, no component matches.

This is the cleanest enforcement of the pedagogy possible — it's not a checklist, it's a type constraint. The pedagogy is encoded in the type system of the renderer.

---

## Open decisions for Sprint 1 kickoff

1. **Brand visual identity finalized?** Sprint 1 can start with placeholders; Sprint 2 needs the real palette + fonts + logo treatments.
2. **Stock footage vendor:** Pexels (free) for Sprint 3 is fine; revisit Storyblocks if Pexels coverage is thin for TikTok-creator-specific topics.
3. **Music bed sourcing:** Epidemic Sound subscription, royalty-free library, or commission a BEA-original track?
4. **Self-host vs Remotion Cloud for renders at scale?** Phase 1 stays local; revisit if monthly rendering volume crosses ~100 modules.


<a id="5-phase-0-spike-runbook"></a>

# 5. Phase 0 Spike Runbook

> Source: `docs/bea-training-engine-spike-runbook.md`

---

# BEA Training Engine — Phase 0 Spike Runbook

> Time-box: **3 days**
> Goal: Produce **one watchable BEA-branded training video** end-to-end from a fixed topic, with no orchestration / personalization / automation.
> Output: Decision memo on whether `training-video-generator` quality is acceptable as-is, or needs significant rework before Phase 1.

> **v0.2 update:** Pivoted from the unofficial `notebooklm-py` fork to the official **NotebookLM Enterprise REST API** (Google Cloud, Preview / v1alpha). Key implications:
> - Auth via `gcloud auth print-access-token`, not session cookies
> - Requires a NotebookLM Enterprise license on your GCP project
> - The Enterprise API exposes notebooks + sources + audio overviews; **slide-deck generation is not a documented output** — Claude derives slides from the audio overview transcript + source corpus
> - Day 1's critical verification is: *can we actually retrieve the audio file and transcript via API?* If not, see §"Day 1 blocker paths" below.
>
> **v0.3 update:** Discovered that `training-video-generator` (the BEA fork) is a doc-prep tool for consumer NotebookLM, not a slide-deck-to-MP4 renderer, AND the NotebookLM Enterprise API doesn't expose video overview generation. See `docs/bea-training-engine-tooling-findings.md` for details. Pivoted the spike's video assembly to a DIY pipeline: PIL slide rendering + Kokoro TTS + ffmpeg. The kit's `src/video_renderer.py` now implements this pipeline directly.

---

## Why this spike exists

The entire Training Engine architecture hangs on one unproven assumption: **the upstream `training-video-generator` fork produces output good enough to be the agency's training videos.**

If yes → continue to Phase 1, full investment justified.
If no → either invest in customization (changes scope significantly) or pivot to a different video-gen approach.

Spending 3 days here saves potentially weeks of building orchestration around a broken core.

---

## Pre-spike checklist

| Item | Status | Notes |
|---|---|---|
| Google Cloud project with **NotebookLM Enterprise license** | ⬜ | This is the gating prereq — see [setup docs](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks) |
| `gcloud` CLI installed + `gcloud auth login` done | ⬜ | Test: `gcloud auth print-access-token` returns a token |
| Project number and region noted | ⬜ | From [console](https://console.cloud.google.com/projectnumber). Region is `us`, `eu`, or `global`. |
| Anthropic API key (Claude does slide derivation) | ⬜ | Set `ANTHROPIC_API_KEY` in `.env` |
| Local Python 3.11+ environment | ⬜ | |
| 1 BEA branding asset bundle | ⬜ | Logo PNG, brand colors hex, intro music if used |
| 1 fixed sample topic chosen | ⬜ | Recommend: *"How to acknowledge a gifter on TikTok LIVE"* — short, well-trodden, easy to evaluate quality |
| 1-3 source documents on the topic | ⬜ | Pull from BEA-Live-Guide; PDF/Markdown is fine |

---

## Day 1 — Setup, notebook, sources, kick audio overview

### Morning: environment

The `bea-training-engine-spike/` kit in this repo automates most of this:

```bash
cd bea-training-engine-spike
gcloud auth login
gcloud auth application-default login
./setup.sh
cp .env.example .env
# Edit .env: GCP_PROJECT_NUMBER, NOTEBOOKLM_LOCATION, ANTHROPIC_API_KEY
source .venv/bin/activate
```

### Afternoon: notebook + sources + kick audio overview

```bash
python src/spike_orchestrator.py auth
python src/spike_orchestrator.py create-notebook --title "BEA Training Spike"
# Drop your source docs into inputs/ first
python src/spike_orchestrator.py upload-sources --inputs inputs/
python src/spike_orchestrator.py kick-audio-overview --topic "..."
```

**End of Day 1 success criteria:**

1. `auth` returns at least one notebook (or empty list) — proves Enterprise API access works
2. `create-notebook` creates a notebook and `state.json` records its ID
3. `upload-sources` uploads at least one source — **note: the sources REST endpoint shape is not yet documented in the page we read; finding it is part of the Day 1 work**
4. `kick-audio-overview` returns success and the audio overview begins async generation

**If blocked:**

- **No Enterprise license**: pause. Either get the license enabled OR switch to the legacy fallback (`USE_LEGACY_NOTEBOOKLM=true`) for the spike only.
- **Sources endpoint unclear**: spend up to 2 hours digging through Discovery Engine docs. If still unclear, file a question with Google support and proceed to Path C below.
- **Audio overview API errors**: capture the error and proceed to Path C (Claude direct).

---

### Day 1 blocker paths

If the Enterprise audio overview path fails or its output isn't retrievable, fall back per this decision tree:

| Symptom | Path | What to do |
|---|---|---|
| ~~Sources endpoint not findable~~ ~~**Path B**~~ | ~~Skip NotebookLM entirely. Use Claude with the source corpus + `prompts/slide-outline.md` to produce the deck directly. Lose the audio-overview voice; gain immediate progress.~~ **Resolved:** sources endpoint is `notebooks/{id}/sources:batchCreate`. For .md/.txt the kit handles it; for PDFs, `uploadFile` shape is the remaining Day 1 unknown — workaround: convert PDFs to .md for the spike. |
| Audio overview generates but neither audio URL nor transcript is in the response | **Path B** | Same. NotebookLM-generated content that we can't retrieve programmatically isn't useful for an automated pipeline. |
| Enterprise license unavailable | **Path C** | Use the unofficial `notebooklm-py` fork via `USE_LEGACY_NOTEBOOKLM=true`. Spike only — never production. |
| Everything works end-to-end | **Path A (default)** | Continue to Day 2 as planned. |

The decision-memo template captures which path you ended up on.

---

## Day 2 — Fetch overview, derive deck via Claude, render video

### Morning: fetch overview + derive deck

```bash
python src/spike_orchestrator.py fetch-audio-overview
```

The orchestrator polls until the audio overview finishes (typically a few minutes), then saves the raw response to `outputs/01-audio-overview.json`. **Open this file and inspect it.** What's in there? Audio URL? Transcript text? Just metadata?

If transcript or audio is present:
- Note the field path; the slide deriver looks for it heuristically but you may need to hand-extract.

If nothing useful is present (just metadata):
- This is the moment to decide: continue with Path B (Claude only) or escalate to Google support.

Then derive the deck:

```bash
python src/spike_orchestrator.py derive-deck --topic "How to acknowledge a gifter on TikTok LIVE"
```

This calls Claude with the transcript (if available) plus the source corpus, producing `outputs/01-deck-spike/deck.json`.

**Sanity check:** Read the script aloud. Does it sound like BEA, or like generic AI mush? Note your gut reaction — this is data for the decision memo. Don't over-iterate prompts — that's a Phase 1 task.

### Afternoon: video render

```bash
python src/spike_orchestrator.py render-video --deck outputs/01-deck-spike/deck.json
```

Read `forks/training-video-generator/README.md` and fill in the TODOs in `src/video_renderer.py` first. Likely needs:

- Slide JSON in the format the generator expects (adapt deck.json shape if needed)
- Narration text per slide
- Brand config (logo path, color palette) from `brand/theme.json`

**End of Day 2 success criterion:** A playable MP4 at `outputs/01-video-spike.mp4`.

---

## Day 3 — Evaluation & decision memo

### Morning: structured evaluation

Watch the video twice. Score on 1-5 (1=unusable, 5=ship it as-is):

| Dimension | Score | Notes |
|---|---|---|
| Visual polish (slide design, transitions, brand fit) | | |
| Narration quality (voice, pacing, pronunciation of "TikTok", "gifter", etc.) | | |
| Script accuracy (does it match BEA's actual guidance?) | | |
| Pacing (right length, no dead air, no rush) | | |
| Educational effectiveness (would a new creator learn from this?) | | |
| Production cost in minutes of human attention | | |
| API/compute cost in USD | | |

Anything 3+: viable with tuning.
Anything 2 or less in **multiple** dimensions: significant rework needed; reconsider stack.

### Afternoon: decision memo

Write a 1-page memo answering:

1. **Quality gate**: Is the output watchable as-is? Acceptable with light tuning? Or does it need significant work?
2. **Easiest wins**: If continuing, what 3 specific tweaks would lift quality fastest? (brand template, voice swap, prompt tweaks, etc.)
3. **Biggest concerns**: What's the dealbreaker risk? (auth flakiness, output quality variance, ToS uncertainty, cost?)
4. **Recommendation**: Go to Phase 1 / Tune & re-spike / Pivot to alternative stack.

Stash the memo at `outputs/spike-decision-memo.md`. Share with the team.

---

## Out of scope for this spike

- Claude orchestration (manual orchestration is fine for one video)
- `mybrain` integration (manual source curation is fine for one video)
- Personalization (V2 anyway)
- CI / hosting / queues
- Distribution to LMS / YouTube / portals
- Multiple topics / batch generation
- Voice or brand customization beyond the bare minimum

Each of these is a Phase 1 task. Don't expand the spike.

---

## Outputs by end of Day 3

| Artifact | Location |
|---|---|
| One playable MP4 | `outputs/01-video-spike.mp4` |
| Slides + narration source files | `outputs/01-deck-spike/` |
| 1-page decision memo | `outputs/spike-decision-memo.md` |
| Updated checklist of what works / what's broken | this doc, inline |

---

## Decision gate

After the memo:

| Memo recommendation | Next action |
|---|---|
| **Go** | Kick off Phase 1 per the main spec |
| **Tune & re-spike** | Allocate 2 more days for the top 3 tweaks; re-evaluate |
| **Pivot** | Investigate alternate video-gen stacks (Synthesia API, HeyGen, custom Remotion build) |

---

## What this runbook is NOT

- Not a Phase 1 plan — that's in the main spec
- Not a production runbook — corners are cut intentionally for speed
- Not a quality benchmark — N=1 video is enough to decide go/tune/pivot, not enough to set quality standards


<a id="6-tooling-findings"></a>

# 6. Tooling Findings

> Source: `docs/bea-training-engine-tooling-findings.md`

---

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


<a id="7-delivery-pipeline-gaps"></a>

# 7. Delivery Pipeline Gaps

> Source: `docs/bea-training-engine-delivery-pipeline-gaps.md`

---

# BEA Training Engine — Delivery Pipeline Gaps

> Context update: BEA training videos will be **hosted on YouTube** and **played inside the Toklytics-LiveIQ app**. This doc inventories logistics gaps on the back half of the pipeline.
>
> **Important framing:** this is a *logistics* gap inventory. Production quality of the videos themselves is tracked separately in `bea-training-engine-quality-strategy.md`. Closing every gap in this doc does NOT mean videos are ready for creators — it means the plumbing works. The quality strategy is the north star; this doc is the substrate that has to function for the strategy to be deliverable.

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

### 3. Thumbnails wired into the pipeline — ✅ RESOLVED
**Status:** `src/thumbnail_generator.py` ships three backends, selectable via `--thumbnail-mode` or the `THUMBNAIL_ENGINE` env var:

| Mode | When it runs | Backend | Pros | Cons |
|---|---|---|---|---|
| `pil` (default) | Pre-upload | Local PIL render | No external service. Deterministic. Brand-consistent across modules. | Plain visual style; no AI imagery. |
| `trpc-text` | Pre-upload | YouTube-Thumbnail service (text_prompt mode) | AI-generated. | Tool can't see the video content yet. Requires service reachable. |
| `trpc-url` | **Post-upload** | YouTube-Thumbnail service (video_url mode) | Tool downloads + analyzes the published video. Highest quality. | Requires video to be on YouTube first; one extra round-trip. |
| `skip` | — | — | YouTube auto-frame. | No control over the visual. |

Pattern B (post-upload `trpc-url`) needed publisher support for a callback — `youtube_publisher.publish()` now accepts `post_upload_thumbnail_fn(video_url) -> Path` and applies the result via `thumbnails.set()` after the video lands.

**Remaining work:** the tRPC wire shape (procedure name + body envelope + response field) is stubbed based on tRPC v11 conventions. Confirm and adjust after inspecting `apps/api/src/trpc/routers/*.ts` in the `YouTube-Thumbnail` repo.

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


<a id="8-editorial-approval-workflow"></a>

# 8. Editorial Approval Workflow

> Source: `docs/bea-training-engine-editorial-workflow.md`

---

# BEA Training Engine — Editorial Approval Workflow

> Working name: **editorial-workflow**
> Status: Draft v0.1
> Goal: Every AI-generated training video is human-reviewed before it goes live on @boldevolution.

---

## Why this exists

AI-generated training that auto-publishes is a brand and compliance risk. Specific failure modes the workflow must catch:

| Failure | Risk |
|---|---|
| Factual inaccuracy / hallucinated BEA advice | Creators get wrong info; agency reputation damage |
| Voice mispronunciation ("TikTok", "gifter", creator handles) | Looks unprofessional; reduces trust in AI-content |
| Off-brand visual or tone | Inconsistent BEA experience |
| TikTok ToS / compliance concerns | Platform pushback; creator account risk |
| Translation errors in Spanish variant | Equal-or-worse versions of all of the above |
| Cost outlier (unexpected spend during generation) | Budget management |

A human reviewer catches these before they reach creators. Once enough modules ship cleanly with the same prompt template, parts of the review can be relaxed (Phase 2).

---

## Scope decision: per-video, not per-batch

**Decision:** every new module is reviewed individually before publish.

**Rationale:**
- Phase 1 is about establishing a quality bar. Trust accrues over time; you don't start at full trust.
- AI generation is non-deterministic. Two videos from the "same" prompt can have different quality.
- Per-video review at BEA's volume (estimated 1-5 modules/week initially) is sustainable for a single reviewer.

**When per-batch becomes viable:** after 50+ modules ship with a < 10% rejection rate from the same prompt-template family, the workflow can switch to per-batch for that family (e.g., "approve all weekly gifting modules generated from template v3").

This is a Phase 2 optimization, not a Phase 1 requirement.

---

## State machine

```
                       ┌─────────┐
                       │  DRAFT  │  ← derive-deck + render-video complete
                       └────┬────┘
                            │ submit for review
                            ↓
                  ┌────────────────────┐
                  │  PENDING_REVIEW    │
                  └─┬─────────┬────────┘
            approve │         │ reject (with reason + optional slide_index)
                    ↓         ↓
            ┌─────────────┐  ┌──────────────┐
            │  APPROVED   │  │   REJECTED   │
            └──────┬──────┘  └──────┬───────┘
                   │                 │ optional: re-derive
                   │ publish hook    │ with rejection hint
                   ↓                 ↓
            ┌─────────────┐  ┌──────────────┐
            │  PUBLISHED  │  │   ARCHIVED   │
            └──────┬──────┘  └──────────────┘
                   │ source docs change
                   ↓
            ┌─────────────┐
            │ DEPRECATED  │  ← regenerate as v2
            └─────────────┘
```

Spanish (and future-language) variants follow the same state machine **independently** of their English parent. An English module can be APPROVED while its Spanish variant is still PENDING_REVIEW. This matters because Spanish review may need a separate Spanish-speaking reviewer.

---

## Approval roles

| Role | Permissions |
|---|---|
| **editor** | Approve / reject any module |
| **senior_editor** | Required co-approver for compliance-tagged modules |
| **admin** | Manage prompt templates, override status, archive published modules |

Compliance-tagged modules (anything touching TikTok ToS, payment regulations, content moderation policy) require a senior_editor's co-sign. Everything else needs one approval.

---

## Reviewer UX

Lives in Toklytics-LiveIQ admin as a "Training Review" tab. The engine doesn't ship this — it ships a contract that the Toklytics team implements.

**List view:**
- Pending modules sorted by submission time
- Columns: Module ID, Title, Topic, Language, Submitted by (always "engine" for now), Submitted at, Cost
- Filters: language, topic tag, compliance-flagged

**Detail view (per module):**
- Inline MP4 player (loaded from R2 / GCS preview URL, NOT YouTube yet)
- Deck inspection panel: each slide's title, bullets, narration text
- Source citation panel: which BEA-Live-Guide sections informed each slide
- AI generation metadata: model used, prompt template version, cost rollup
- Captions preview (English + Spanish if available)
- Three buttons: **Approve**, **Reject with reason**, **Request changes**

**Reject form fields:**
- Reason (dropdown): factual / mispronunciation / off-brand / off-topic / compliance / cost / **pedagogy** / other
- Slide index (optional): which slide is the problem
- Free-text notes

**Pedagogy compliance checklist** (see `bea-training-engine-pedagogy.md`) — every approved module must satisfy:

**Structure (10-section lesson):**
- [ ] Slide 1 is a `hook` — recognizable scene, no "welcome"
- [ ] All 10 lesson sections covered (or explicit N/A for very short modules): Why This Matters / Core Principle / What This Looks Like On LIVE / How To Apply / Common Mistakes / Pro Tip / Quick Win Challenge / Reflection / Success Checkpoint
- [ ] Closing trio present in order: `action` → `reflection` → `checkpoint`

**Psychology Mode:**
- [ ] `psychology_analysis` sibling JSON exists and is topic-specific (not generic — could not swap topic and have it still apply)
- [ ] Each `why` / `mistake` / `action` slide traces back to a barrier or motivator from the analysis
- [ ] The `adaptation_strategy` is reflected in actual slide choices (not just declared then ignored)

**Behavioral framing:**
- [ ] Every `why` slide ties to money / growth / visibility / loyalty / confidence / consistency
- [ ] Every `checkpoint` includes a quantified metric + duration
- [ ] Every `action` references next LIVE specifically (not "soon" or "eventually")
- [ ] Every `pro_tip` adds real insight beyond the basic `how` (not a restatement)

**Tone + style:**
- [ ] No corporate filler ("in this video", "it's important to note", "studies have shown")
- [ ] Pattern variety — no 3+ same `kind` slides in a row
- [ ] Length matches target ±10%

Modules failing any of the above are rejected with reason `pedagogy`. The rejection feedback loop in `slide_deriver.py` reads the specific pedagogy failure and adjusts the next generation pass.

**Request changes:**
- Same fields as reject, but module goes back to DRAFT instead of REJECTED, with the rejection hint attached for the next generation pass.

---

## Data model

Lives in Toklytics-LiveIQ's existing DB (per BEA confirmation that the Training structure exists there).

```sql
-- New table or extension of the existing module table
CREATE TABLE module_review (
    module_id            text PRIMARY KEY,           -- BEA-TRN-0001, etc.
    language             text NOT NULL,              -- en-US, es-US
    status               text NOT NULL,              -- DRAFT|PENDING_REVIEW|APPROVED|REJECTED|PUBLISHED|DEPRECATED|ARCHIVED
    artifact_url         text NOT NULL,              -- preview MP4 in R2/GCS
    deck_url             text NOT NULL,              -- deck.json in R2/GCS
    timing_url           text,                       -- timing.json
    captions_url         text,                       -- SRT
    thumbnail_url        text,
    source_commit_sha    text,                       -- BEA-Live-Guide version
    prompt_template_ver  text,                       -- e.g. "slide-outline:v3"
    ai_cost_usd          numeric,
    submitted_at         timestamptz NOT NULL,
    submitted_by         text NOT NULL DEFAULT 'engine',
    decided_at           timestamptz,
    decided_by           text,                       -- editor user ID
    decision_reason      text,                       -- if rejected
    decision_slide_index integer,                    -- if rejected at a specific slide
    decision_notes       text,
    compliance_flagged   boolean NOT NULL DEFAULT false,
    youtube_video_id     text                        -- set when status -> PUBLISHED
);

CREATE TABLE module_review_audit (
    id           bigserial PRIMARY KEY,
    module_id    text NOT NULL,
    actor        text NOT NULL,
    action       text NOT NULL,                      -- submit|approve|reject|request_changes|publish|archive
    from_status  text,
    to_status    text NOT NULL,
    notes        text,
    occurred_at  timestamptz NOT NULL DEFAULT now()
);
```

Every transition writes an audit row. No status changes without an audit trail.

---

## Engine-side contract

The engine doesn't own the dashboard, but it does:

1. **Submit modules** for review (state DRAFT → PENDING_REVIEW) by calling Toklytics's tRPC endpoint with the artifacts.
2. **Gate publish** on `status == APPROVED` before calling `youtube_publisher.publish()`.
3. **Apply rejection hints** in subsequent generation passes (read `decision_reason` + `decision_slide_index` and pass into Claude's `slide_deriver` as a "previously rejected with this reason — avoid that issue" addendum).
4. **Honor compliance flag**: when a deck is detected to contain compliance-sensitive content (keyword filter or LLM classifier), set `compliance_flagged = true` on submission so the dashboard knows to require a senior editor.

For the spike + local development, a CLI scaffold (`src/module_status.py`) stores state in a local JSON file (`outputs/review-state.json`) instead of hitting Toklytics. That's enough to validate the contract before the LiveIQ team builds the dashboard.

---

## Compliance flagging

Heuristic v1 (keyword match against the deck's narration):

```python
COMPLIANCE_KEYWORDS = [
    # Payments / payouts
    "payout", "earnings", "income", "tax", "refund", "chargeback",
    # Platform policy
    "violation", "ban", "strike", "appeal", "shadow", "shadowban",
    # Disclosure / promotion
    "sponsor", "ad", "promotion", "endorsement", "ftc", "disclose",
    # Underage / safety
    "minor", "child", "underage", "safety",
]
```

If any keyword appears in the deck's narration text, set `compliance_flagged = true`. False positives are acceptable; the cost is one extra reviewer click. False negatives are not acceptable.

LLM-based classifier is a Phase 2 upgrade.

---

## Rejection feedback loop

Every rejection produces a structured note that the next regeneration pass uses:

```json
{
  "rejection_reason": "mispronunciation",
  "slide_index": 4,
  "notes": "Kokoro pronounces 'TikTok' as 'tick-tock' awkwardly. Switch to Cloud TTS for this module."
}
```

The orchestrator's `derive-deck` command checks for a sibling `rejection.json` in the deck directory; if present, it appends the rejection summary to the system prompt as: *"This deck was previously rejected: ${reason}. Avoid the issue at slide ${slide_index}."*

For pronunciation issues specifically, the renderer can read `rejection.json` and override the voice / engine for the next render.

---

## Notifications

When a module hits `PENDING_REVIEW`:

- In-app notification in Toklytics-LiveIQ admin to editors
- Optional Slack webhook (`SLACK_REVIEW_WEBHOOK` env var) for teams that prefer chat
- Daily digest at 9am local time of everything still pending

When a module is approved or rejected:

- Audit log entry (always)
- If `submitted_by == "engine"`, the engine receives a webhook to trigger publish or to apply the rejection hint

---

## Failure modes & escalation

| Scenario | Behavior |
|---|---|
| Module stuck in PENDING_REVIEW > 7 days | Escalation notification to admin |
| Same module rejected 3x with same reason | Lock further auto-regeneration; flag for prompt-template review |
| Reviewer disagreement (approve, then later flag as bad) | Audit log preserves both; module goes to DEPRECATED, regenerate as v2 |
| All editors unavailable | Admin can manually override and publish, but the audit log captures this |

---

## Phase 1 implementation plan

| Step | Owner | Effort |
|---|---|---|
| Define `module_review` + `module_review_audit` tables in Toklytics-LiveIQ | LiveIQ team | 1 day |
| Engine-side `module_status.py` state machine (CLI for local dev) | Engine team | 1 day |
| Engine submits to Toklytics tRPC endpoint after render | Engine + LiveIQ | 2 days |
| Reviewer dashboard tab in Toklytics-LiveIQ admin | LiveIQ team | 5-7 days |
| Notifications (in-app digest + optional Slack) | LiveIQ team | 2 days |
| Engine consumes approval webhook + triggers publish | Engine team | 1 day |
| Rejection hint loop in `slide_deriver.py` + `video_renderer.py` | Engine team | 2 days |

**Total:** ~2 weeks of focused work split between the engine and LiveIQ teams.

---

## Phase 2 optimizations

- Per-batch approval for trusted prompt templates
- LLM-based compliance classifier (replace the keyword heuristic)
- Quality-trust scoring per template (auto-approve when historical rejection rate < 5%)
- A/B testing inside the workflow: ship two variants of the same module, see which retains better, archive the loser
- Reviewer-facing "what changed since last version?" diff for deprecated → regenerated modules

---

## Open questions

1. **Who are the initial editors?** Names + permissions. Affects role setup.
2. **Senior editor for compliance — separate human or same person until volume justifies?** Likely same person at launch; spec calls out the separation for future-proofing.
3. **Where do preview MP4s live before publish?** R2 (since BEA has it) seems natural — short-lived signed URLs valid for the review window.
4. **Slack webhook in scope?** If yes, need a workspace + channel + webhook URL.
5. **What's the SLA for review turnaround?** Affects the stale-review escalation threshold.

---

## Decision recap

| Question | Answer |
|---|---|
| Per-video or per-batch? | Per-video at launch. Per-batch as Phase 2 optimization. |
| Where does the dashboard live? | Toklytics-LiveIQ admin (uses existing structure) |
| Compliance gating? | Keyword-based flag; senior editor co-sign required |
| Spanish variants reviewed separately? | Yes, independent state machines |
| Rejection feedback loop? | Yes; structured rejection.json informs next regen |


<a id="9-google-apis-inventory"></a>

# 9. Google APIs Inventory

> Source: `docs/bea-training-engine-google-apis.md`

---

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


<a id="10-toklytics-liveiq-security-audit"></a>

# 10. Toklytics-LiveIQ Security Audit

> Source: `docs/toklytics-liveiq-security-audit-spec.md`

---

# Toklytics-LiveIQ Pre-Launch Security Audit — Plan

> Working name: **toklytics-liveiq-security-audit**
> Status: Draft v0.2
> Target: `Toklytics-LiveIQ` (single repo)
> Tooling lead: `reaper` (forked) + standard SAST/DAST stack

> **Scope correction from v0.1:** The repos `portal-uk`, `portal-us-ca`, and `BEA_Creator_Portal` are **dead** — their functionality was consolidated into `Toklytics-LiveIQ`. The audit now targets one codebase with multi-region tenancy, not three portals. See §10 for cleanup of the dead repos.

---

## 1. Why this exists

`Toklytics-LiveIQ` is now the single asset holding:

- Creator PII (legal name, address)
- Multi-region data subject to GDPR (UK), CCPA (CA — California), PIPEDA (Canada)
- Authentication credentials and session tokens
- Live realtime coaching data (per your existing integration)
- File uploads (CSVs, screenshots feeding into the analytics layer)
- Per-creator historical reports

Stripe lives in a separate, **completely independent** application — `KLING-Director` — so all payment-flow audit items move to a parallel spec (see §11). LiveIQ and KLING-Director do not integrate, share data, or share auth. The LiveIQ audit covers no payment-related surface.

Because everything is consolidated into one app, the **blast radius of a breach is larger** than it would have been across three smaller portals. One bug here can expose every creator. A breach would be reputationally fatal for an agency whose value prop depends on creator trust. A pre-launch audit (or pre-next-major-release audit, if LiveIQ is already live) is a fixed-cost, fixed-time investment that reduces this risk.

This is **not** a continuous penetration testing program. It's a one-time gated review with remediation.

---

## 2. Scope

| In scope | Out of scope (this pass) |
|---|---|
| Toklytics-LiveIQ web app + APIs | Cloudflare config audit, full IaC review |
| Authentication + session management | KLING-Director (separate app, separate audit — see §11) |
| Per-region tenancy + data residency handling | Anything payment-related (KLING-Director is the only app with Stripe) |
| File uploads (CSV, screenshots) | The dead portal repos (archive them — see §10) |
| Live realtime coaching data path | Social engineering / phishing simulations |
| Role-based access (if staff use the same app) | Continuous bug bounty (separate post-launch decision) |
| TikTok API integration (if any) | Underlying TikTok platform behavior |

---

## 3. Threat model (STRIDE shorthand)

| Threat | Concern level | Specific risk |
|---|---|---|
| **S**poofing | High | Account takeover via weak auth, credential stuffing |
| **T**ampering | Medium | Manipulating payout requests, modifying creator metrics |
| **R**epudiation | Medium | Disputed payouts without audit logs |
| **I**nformation disclosure | **Critical** | Cross-tenant data leak between creators; PII exposure |
| **D**enial of service | Low for v1 | Rate limit absence on expensive endpoints |
| **E**levation of privilege | High | Regular creator escalating to admin |

The two critical risks for this kind of app are almost always (a) cross-tenant data leak (creator A sees creator B's data) and (b) auth bypass. Allocate the most audit time there.

**Consolidation amplifies these risks** — when three portals were separate, an IDOR bug in one didn't expose the others. In LiveIQ, a single IDOR could expose every region's creator data. Multi-region tenancy enforcement deserves extra audit time beyond a typical multi-tenant SaaS review.

---

## 4. Audit phases

### Phase 1 — Recon (1-2 days)

- [ ] Inventory every endpoint (REST/GraphQL/tRPC)
- [ ] Inventory every public-facing route
- [ ] Map all third-party integrations (TikTok API, Cloudflare, Supabase, NotebookLM if connected, etc.)
- [ ] Document the auth flow end-to-end (sequence diagram)
- [ ] Document the tenancy model — how the app distinguishes UK vs US vs CA creators at the DB / API layer
- [ ] List every place PII flows (input → storage → display → logs)
- [ ] Trace the Live realtime coaching data path (websocket / SSE / poll? where does the data sit?)

**Deliverable:** Attack surface map (markdown + diagram).

---

### Phase 2 — Automated scanning (1-2 days)

| Tool | What it checks |
|---|---|
| **`reaper`** (your fork) | Live validation proxy — record app usage, replay with mutations to test auth/IDOR/injection |
| **Semgrep** (cloud free tier) | SAST — secrets, OWASP patterns in code |
| **OWASP ZAP** baseline scan | DAST — passive scan against staging |
| **npm audit** / **pnpm audit** / **pip-audit** | Dependency CVEs |
| **GitHub secret scanning** (already enabled) | Leaked credentials in history |
| **Trivy** | Container image CVEs (if LiveIQ ships Docker) |
| **gitleaks** | Pre-commit secrets check (install if missing) |

**Deliverable:** Raw findings exported per tool. Tagged severity (Critical / High / Medium / Low / Info).

---

### Phase 3 — Manual review (3-5 days, the highest-value phase)

Focus on what scanners miss:

#### Authentication & session
- [ ] Password reset flow can't be abused (no user enumeration, tokens single-use, time-bound)
- [ ] Session fixation / re-use after logout
- [ ] MFA enforced for high-value actions (changing payout info)
- [ ] OAuth/social-login state parameter validated
- [ ] JWT signing key rotation possible; algorithm pinned

#### Authorization (the #1 risk — IDOR + tenant isolation)
- [ ] Every `/api/creators/:id/*` endpoint checks `id == session.userId` server-side
- [ ] Every list endpoint filters by tenant *and region*, not just by `WHERE NOT deleted`
- [ ] Admin-only endpoints fully blocked for non-admin sessions
- [ ] Test with two real creator accounts in parallel: account B should never see account A's data even with manipulated IDs
- [ ] Test cross-region access — a UK creator should not be able to read US creator data via path/param tampering
- [ ] Live coaching feed scoped to the creator's own LIVE session — no eavesdropping on other creators' streams

#### Data handling
- [ ] PII fields encrypted at rest (Supabase column-level encryption or pgcrypto)
- [ ] Logs scrubbed of PII (no full request bodies with personal data)
- [ ] Data export endpoint exists (GDPR Article 20)
- [ ] Data deletion endpoint exists (GDPR Article 17, CCPA right to delete)
- [ ] Retention policy documented and enforced (auto-purge inactive accounts after N years)
- [ ] Data residency: UK/EU creator data stored in EU region if claimed in privacy policy

#### File uploads (CSVs, screenshots)
- [ ] Server-side MIME type + magic byte validation, not just extension
- [ ] Max size enforced before parse
- [ ] CSV parsing uses a streaming parser, not whole-file load
- [ ] No SSRF via uploaded URLs
- [ ] Uploaded files served from a different origin than the app (prevent XSS via uploaded SVG/HTML)

#### Common web bugs
- [ ] CSRF tokens on all state-changing same-origin POSTs (or SameSite=Lax+ cookies)
- [ ] CSP header set, no `unsafe-inline` scripts
- [ ] XSS: every user-rendered string escaped (React handles most, but `dangerouslySetInnerHTML` audit)
- [ ] Clickjacking: `X-Frame-Options: DENY` or CSP `frame-ancestors`
- [ ] Open redirect on login/logout redirect params

**Deliverable:** Findings doc with reproduction steps, severity, suggested fix per finding.

---

### Phase 4 — Remediation (varies; budget 1-3 weeks)

- [ ] Triage findings: Critical/High block launch; Medium scheduled; Low/Info backlog
- [ ] Each finding gets a ticket with owner and target date
- [ ] Re-test after fix before closing

**Deliverable:** Findings closed, retest evidence attached.

---

### Phase 5 — Final gate (1 day)

- [ ] No Critical or High findings open
- [ ] All Medium findings have scheduled fix dates
- [ ] Penetration test report signed off
- [ ] Privacy policy + DPA in place (UK + EU creators especially)
- [ ] Incident response runbook drafted (who gets paged, how breach is communicated)

**Deliverable:** Go/no-go memo for LiveIQ.

---

## 5. `reaper` role in detail

Your fork: live validation proxy for testing web app vulnerabilities.

**How we use it:**

1. Stand up Toklytics-LiveIQ in staging with seeded test data covering all regions (Creator-UK, Creator-US, Creator-CA, Admin).
2. Route browser traffic through `reaper` while exercising every feature as Creator-UK.
3. `reaper` captures the full request/response set.
4. Replay captured requests with mutations:
   - Swap `:id` in URLs to other creators' IDs (same region, then cross-region)
   - Strip `Authorization` header
   - Replay with another creator's session cookie
   - Tamper with body params (amounts, dates, role flags, region codes)
5. Flag any non-403/401 response on a tampered request.

This catches the IDOR class of bugs efficiently — the single highest-value bug class for multi-tenant SaaS. The cross-region mutation pass is the highest-value addition here, given that LiveIQ now serves all regions from one codebase.

**Setup steps:**

```bash
git submodule add https://github.com/BEA-BOLD-EVOLUTION/reaper.git tools/reaper
# Configure reaper to record from staging.liveiq.bea.com
# Use the replay script in tools/reaper/scripts/
```

If the upstream `reaper` doesn't have a replay-with-mutation feature, that's a small custom script (~100 LOC) on top of its captured-request format.

---

## 6. Out of scope (this pass)

- Infrastructure penetration testing (Cloudflare, Supabase configs — separate audit)
- Social engineering / phishing simulations
- Full PCI-DSS audit (Stripe Checkout keeps you out of scope by design)
- Continuous bug bounty program (recommended *after* launch, separate decision)

---

## 7. Estimated effort

| Phase | Effort |
|---|---|
| Phase 1 Recon | 1-2 days |
| Phase 2 Automated scans | 1-2 days |
| Phase 3 Manual review | 3-5 days |
| Phase 4 Remediation | 1-3 weeks (depends on findings) |
| Phase 5 Final gate | 1 day |
| **Total elapsed** | **2-4 weeks** for one engineer |

Single codebase = single audit. The "3-5 weeks per portal × 3" estimate from v0.1 collapses to one pass.

---

## 8. Open questions

1. Is Toklytics-LiveIQ already live with real creator data, or is this truly pre-launch? *(If already live, this becomes a "first-pen-test of an in-production app" — same plan, but Phase 4 remediation needs coordinated deploys.)*
2. Internal vs external auditor — running it yourself with `reaper` + Semgrep is fine for a v1 launch; a paid 3rd-party pen test before scaling to thousands of creators is recommended.
3. Bug bounty program plan post-launch?
4. Data residency claim — does the privacy policy promise UK data stays in EU? If yes, the audit must verify this is enforced in infrastructure.

---

## 9. Next concrete steps

1. Confirm whether LiveIQ is pre-launch or live (§8 Q1).
2. Stand up `reaper` against LiveIQ staging as a Phase 0 trial run.
3. Run Phase 1 Recon.

---

## 10. Cleanup — dead portal repos

The repos `portal-uk`, `portal-us-ca`, and `BEA_Creator_Portal` are confirmed dead (their functionality was absorbed into Toklytics-LiveIQ). Recommended actions:

- [ ] Archive each repo on GitHub (Settings → Archive). Preserves history, prevents accidental clones, signals "do not use".
- [ ] Add a final commit to each with a `README.md` line: *"Archived. Functionality consolidated into Toklytics-LiveIQ as of YYYY-MM-DD."*
- [ ] Remove any CI / deploy jobs still wired to them.
- [x] ~~Revoke any service-account credentials those repos held~~ **Confirmed rotated.**

The remaining items are housekeeping — the security-critical step (credential rotation) is done.

---

## 11. Sibling audit: KLING-Director

`KLING-Director` is a **completely separate application** with its own audit spec at `kling-director-security-audit-spec.md`. It holds all Stripe surfaces (subscription billing + Connect Express affiliate payouts), AI cost exposure (Anthropic, Gemini), tier-gating, and file-upload concerns. None of that surface exists in LiveIQ.

The two audits can run in parallel with one engineer per audit, or sequentially with the same engineer (1-week gap between to context-switch cleanly). Shared infrastructure: one `reaper` setup with two separate replay configs, shared Semgrep base config extended per app.


<a id="11-toklytics-liveiq-mobile-wrapper"></a>

# 11. Toklytics-LiveIQ Mobile Wrapper

> Source: `docs/toklytics-liveiq-mobile-wrapper-spec.md`

---

# Toklytics-LiveIQ Mobile Wrapper — Plan

> Working name: **liveiq-mobile**
> Status: Draft v0.2
> Target: iOS + Android wrapper around `Toklytics-LiveIQ`
> Tooling lead: `full_web_converter_To_flutter_App` (forked)

> **Scope correction from v0.1:** The repos `portal-uk`, `portal-us-ca`, and `BEA_Creator_Portal` are dead — their functionality was consolidated into `Toklytics-LiveIQ`. The wrapper targets one web app, not three. Region differentiation is already handled inside LiveIQ, so no app-side region picker is needed.

---

## 1. Why this exists

Creators live on their phones. A mobile-installed app changes engagement vs a bookmarked PWA in three concrete ways:

1. **Push notifications** — payout posted, LIVE schedule reminder, new training module, gift milestone hit, realtime coach alerts
2. **Home screen presence** — LiveIQ is one tap away, not three navigation steps
3. **App store credibility** — for an agency, having an iOS+Android app signals legitimacy to new creators

A Flutter wrapper around the existing LiveIQ web app is the fastest path to all three without rebuilding the UI natively. The forked `full_web_converter_To_flutter_App` is designed for exactly this conversion.

---

## 2. Scope

### In scope (v1)
- Single Flutter app wrapping Toklytics-LiveIQ
- Native push notifications
- Biometric / native auth on app open
- Deep linking from emails / SMS into specific LiveIQ screens
- Offline detection + graceful fallback screens
- iOS + Android distribution

### Out of scope (v1)
- Native UI replacement (we wrap web, we don't rewrite)
- Tablet-optimized layouts (portrait phone only)
- Apple Watch / Wear OS companions
- In-app purchases (Apple/Google would take 30% of any payout flow — keep payments web-only)
- Region picker — LiveIQ already routes by creator profile, not by app variant

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FLUTTER APP (single binary)                                │
│  - Native auth shell (biometric, secure storage)            │
│  - Push notification handler                                │
│  - Deep link router                                         │
│  - WebView host (flutter_inappwebview)                      │
└────────────────────────────┬────────────────────────────────┘
                             │ JS bridge
                             ↓
┌─────────────────────────────────────────────────────────────┐
│  TOKLYTICS-LIVEIQ (existing web app)                        │
│  - Detects "in BEA app" via UA string                       │
│  - Hides web-only chrome (browser back, footer)             │
│  - Calls bridge for native features (push opt-in, biometric)│
│  - Routes user by their profile region (no app-side switch) │
└─────────────────────────────────────────────────────────────┘
```

LiveIQ stays the source of truth. The Flutter shell adds native capabilities and store distribution. Total native code stays under ~2000 LOC since multi-portal complexity is gone.

---

## 4. Module breakdown

### 4.1 Flutter shell (this new repo)

Built from `full_web_converter_To_flutter_App` as starting point. Likely customizations:

- Single target URL (Toklytics-LiveIQ production / staging)
- BEA brand splash + theme
- Replace generic WebView with `flutter_inappwebview` for the JS bridge
- Add `firebase_messaging` for push (FCM works on both platforms)
- Add `local_auth` for biometrics
- Add `app_links` for deep linking

### 4.2 Toklytics-LiveIQ additions

LiveIQ needs a small "mobile mode" addition:

- Detect UA: `BEA-Mobile/1.0`
- Apply `.in-app` CSS class to hide elements that don't make sense in-app (browser back button, footer with marketing links)
- Expose JS calls that the bridge intercepts: `bea.registerPush()`, `bea.requestBiometric()`, `bea.openExternal(url)`

Coordinate with whoever owns the LiveIQ repo so this lands ~1 sprint before the mobile MVP needs it.

### 4.3 Push notification backend

Cloudflare Worker or Supabase Edge Function that:

- Receives event triggers (payout posted, LIVE schedule change, training video ready)
- Looks up creator's FCM tokens (stored on portal sign-in)
- Sends push via FCM HTTP v1 API

Server-side, not in this repo's scope — but the Flutter side registers tokens and the portals provide the trigger events.

---

## 5. Distribution

### iOS
- Apple Developer Program membership ($99/year per org)
- App Store Connect listing
- Privacy nutrition labels (must declare every data type the wrapped web app collects)
- Sign-in with Apple required if any other social login is offered
- Age rating: likely 17+ given creator/streaming domain — confirm
- App Tracking Transparency prompt if any analytics SDK tracks across apps

### Android
- Google Play Developer account ($25 one-time)
- Play Console listing
- Data Safety form (similar to Apple's privacy labels)
- Target API level kept current (Play enforces a rolling minimum)

### Compliance gotchas to verify before submission
- **Apple §4.7 "minimum functionality"**: Pure web wrappers can be rejected. Solution: native push, biometric, deep links, and offline screen are enough native features to clear this.
- **Google "spam" policy**: Same concern. Same solution.
- **Both stores**: TikTok-adjacent apps face extra scrutiny. Be very clear in the listing this is a *creator portal* for an agency, not a TikTok client.
- **GDPR + UK GDPR**: Privacy policy URL must be in store listing. Already required by §portal-security-audit-spec.
- **Push notification permissions**: iOS 13+ requires explicit opt-in. Android 13+ requires runtime permission.

---

## 6. Phased rollout

### Phase 0 — Spike (3 days)

Goal: Prove `full_web_converter_To_flutter_App` can wrap Toklytics-LiveIQ with a WebView and load it on an iOS Simulator + Android Emulator.

- Clone fork
- Configure with the LiveIQ staging URL
- Brand splash, smoke test
- Verify session cookies persist across app launches
- Test the trickiest UX paths: CSV upload, screenshot upload, live coaching feed (websocket / SSE)

**Deliverable:** A `.apk` + `.app` on dev machines, demoed.

**Decision gate:** Is the WebView UX acceptable? Specifically: scrolling, keyboard handling, file pickers, camera access for screenshot uploads, realtime coaching feed stability inside a WebView.

---

### Phase 1 — MVP (2-3 weeks)

- [ ] BEA brand theming
- [ ] Native auth shell with biometric lock
- [ ] FCM push notifications (registration + receive)
- [ ] Deep linking (`https://m.bea.com/...` → app)
- [ ] Offline screen
- [ ] CI: build pipeline for both platforms (Codemagic, Bitrise, or GitHub Actions)

Faster than v0.1's estimate because the multi-portal selector / region routing complexity is gone.

**Deliverable:** TestFlight + Play Internal Testing builds installable by the BEA team.

---

### Phase 2 — Store submission (2-4 weeks elapsed, mostly waiting on reviews)

- [ ] Privacy policy + DPA finalized
- [ ] App Store + Play Store listings drafted (copy, screenshots, video preview)
- [ ] Privacy labels / Data Safety form completed
- [ ] Submit to App Store + Play Store
- [ ] Handle review feedback (expect 1-2 rounds)

**Deliverable:** Apps published.

---

### Phase 3 — Post-launch

- Auto-update mechanism (CodePush or similar, optional)
- Analytics (privacy-respecting — Plausible/PostHog, not GA)
- Crash reporting (Sentry)
- A/B test push notification copy/timing

---

## 7. Tech stack decisions

| Layer | Choice | Rationale |
|---|---|---|
| Framework | Flutter | Single codebase, your fork is already Flutter-based |
| WebView | `flutter_inappwebview` | Most capable bridge; better than the official one |
| Push | Firebase Cloud Messaging | Works on both platforms, free at this scale |
| Auth shell | `local_auth` (biometrics) + `flutter_secure_storage` | Keychain / Keystore backed |
| Deep links | `app_links` | Universal Links + App Links |
| State | Riverpod or Bloc | Either fine; pick one team preference |
| CI | GitHub Actions + Codemagic for iOS signing | Free tier handles low volume |
| Distribution | TestFlight + Play Internal Testing for staging | Standard |

---

## 8. Cross-cutting dependency: `toklytics-liveiq-security-audit-spec.md`

**A mobile wrapper inherits every web vulnerability.** If the audit finds Critical or High issues, the mobile launch slips with the web launch. Plan the security audit and the mobile wrapper as parallel workstreams gated by the same go-live decision.

Specifically, mobile adds these *new* security considerations on top of the audit:

- [ ] WebView doesn't expose JS bridge methods that grant capabilities the website itself doesn't have (review `bea.*` bridge surface)
- [ ] Certificate pinning for LiveIQ API calls (prevent MITM on hostile WiFi)
- [ ] Jailbreak / root detection (optional — low value vs effort for v1)
- [ ] Deep link handlers validate the URL before navigation (prevent UXSS via crafted deep links)
- [ ] App Transport Security configured (no `NSAllowsArbitraryLoads`)
- [ ] Android `usesCleartextTraffic: false`

Add these to the audit's Phase 3 checklist before mobile launch.

---

## 9. Risks & open questions

| Risk | Mitigation |
|---|---|
| Store rejection for "minimum functionality" | Phase 1 adds enough native features (push, biometric, deep links, offline) to clear this. Document the native-only features in the store listing copy. |
| WebView UX feels janky | Phase 0 spike answers this before further investment. |
| Maintenance burden of one more repo | Single binary, web portals carry the UI updates — Flutter shell rarely changes after v1. |
| TikTok-adjacent rejection risk | Lead with "creator agency portal" framing in the listing, avoid the word "TikTok" in the app name and primary description. |
| Apple/Google policy changes | Acceptable risk; affects everyone equally. |

**Open questions:**

1. ~~One single app with region picker, or three branded apps?~~ **Resolved by scope correction** — one app wrapping LiveIQ, region routing inside the web app.
2. Native deep links require domain ownership of `m.bea.com` (or similar). Is that domain available / planned?
3. Push notification opt-in flow: on first launch (early, low conversion) or after first meaningful action (later, higher conversion)?
4. Is the agency comfortable with the 17+ rating likely required, or do we need to scrub anything that pushes the rating up?
5. Are creators expected to install this themselves, or will the agency push it via onboarding?
6. Does Toklytics-LiveIQ's realtime coaching feed work reliably inside a WebView? (Answered during Phase 0 spike.)

---

## 10. Concrete next steps

1. Phase 0 spike — 3 days to validate WebView UX works for the actual LiveIQ screens (especially CSV/screenshot upload + the realtime coaching feed, which are the riskiest).
2. Decision gate after spike — go/no-go before committing to Phase 1.
3. If go: create `liveiq-mobile` repo, scaffold per §3, set up TestFlight + Play Internal Testing.
4. Coordinate with `toklytics-liveiq-security-audit-spec.md` work so mobile launch isn't blocked at the end by surprises from the audit.


<a id="12-kling-director-security-audit"></a>

# 12. KLING-Director Security Audit

> Source: `docs/kling-director-security-audit-spec.md`

---

# KLING-Director Pre-Launch Security Audit — Plan

> Working name: **kling-director-security-audit**
> Status: Draft v0.2
> Target: `KLING-Director` ([repo](https://github.com/BEA-BOLD-EVOLUTION/KLING-Director))
> Tooling lead: `reaper` (forked) + standard SAST/DAST stack + Stripe-specific checks
> Companion to: `toklytics-liveiq-security-audit-spec.md`

> **Confirmed scope (from README):** KLING-Director is a self-service SaaS web app — an AI-powered prompt compiler for Kling video generation. Users sign up via Supabase Auth, pay via Stripe subscription ($5.99 Director / $9.99 Director Pro / $0 VIP / $0 BEA Creator partner / 7-day free trial). The app uses Claude Sonnet 4 + Gemini 2.0 Flash for prompt analysis. **Two distinct Stripe surfaces:** (a) subscription billing (incoming) and (b) Stripe Connect Express for affiliate payouts at 15% commission (outgoing). Tech stack: Next.js 16, React 19, tRPC 11, Supabase (Auth + Storage + Postgres), Prisma 5, hosted on Vercel (web) + Railway (api).

---

## 1. Why this exists — and why it's separate from the LiveIQ audit

Payment-handling code carries a fundamentally different risk profile than analytics code:

| Risk dimension | LiveIQ (analytics) | KLING-Director (payments) |
|---|---|---|
| Worst-case bug | Data leak | Direct financial loss + chargeback liability |
| Regulator interest | GDPR / CCPA | PCI-DSS scope check, anti-money-laundering posture, payout reporting |
| Recovery from breach | Apologize, rotate creds, notify | Reverse transactions, refund creators, possibly legal exposure |
| Bug bounty value (post-launch) | High | Very high |

A separate audit pass keeps the threat model focused. Two specs > one mega-spec because the auditor's mindset is different per pass.

---

## 2. Scope

| In scope | Out of scope (this pass) |
|---|---|
| KLING-Director web app + tRPC API | Cloudflare config audit, full IaC review |
| **Subscription billing** — Stripe Checkout, webhook handler, trial/upgrade/cancel flows | Underlying Stripe platform behavior |
| **Affiliate payouts** — Stripe Connect Express onboarding, attribution, commission calc, transfers | Full PCI-DSS certification (Stripe Checkout / Elements keeps you out of scope by design) |
| Stripe API key handling + rotation posture | Social engineering / phishing simulations |
| Stripe coupon / promotion code usage (`STRIPE_COUPON_VIP`, `STRIPE_COUPON_BEA_CREATOR`) | Continuous bug bounty (separate post-launch decision) |
| Refund / dispute / chargeback handling | Vercel / Railway platform configs (separate IaC audit) |
| Audit log of every state-changing payment event | |
| Authentication on payment-affecting endpoints | |
| Idempotency posture across all webhook + payout paths | |
| **Tier-gating enforcement** — daily AI quotas, element/preset limits, Pro-only features, retention windows | |
| **AI cost abuse** — Anthropic + Gemini API key handling, rate limits, quota enforcement | |
| **File upload** — 100MB videos, 4 formats, Supabase Storage abuse vectors | |
| Affiliate fraud — self-referral, attribution-window manipulation, cookie/click stuffing | |

---

## 3. Threat model

| Threat | Concern level | Specific risk |
|---|---|---|
| **S**poofing | **Critical** | Forged Stripe webhook triggers fake subscription state change or affiliate payout |
| **T**ampering | **Critical** | Affiliate self-refers and earns commission on own subscription; user manipulates tier via client-side flag |
| **R**epudiation | High | Disputed transfer to affiliate with no audit log; missing trail for subscription tier changes |
| **I**nformation disclosure | High | Stripe customer/account IDs leaked cross-user; affiliate dashboard exposes other affiliates' codes/earnings |
| **D**enial of service | **High for AI** | Trial user burns through Anthropic/Gemini quota costing thousands in API fees; webhook replay creating duplicate transfers |
| **E**levation of privilege | **Critical** | Trial/Director user accesses Pro-only features (video analysis, API, white-label) via client tampering |

**The four highest-priority audit findings for KLING specifically** are:

1. **Unverified Stripe webhook signatures** — the textbook bug. Stripe's docs make this trivially fixable; the bug appears in ~30% of new integrations. KLING has subscription webhooks AND Connect webhooks — both must be verified.
2. **Client-trusted tier / feature flag** — UI sends `{ tier: "pro" }` instead of server reading the subscription state from Supabase. Attacker bypasses paywalls.
3. **AI cost abuse** — no per-user daily quota enforcement on Anthropic / Gemini calls means one bad actor can drain thousands in API spend before you notice.
4. **Affiliate self-referral** — same email / payment method / device / IP as the referrer earning 15% commission on their own subscription. Common pattern, hard to catch retroactively.

Allocate the most audit time to those four.

---

## 4. Audit phases

### Phase 1 — Recon (1-2 days)

- [ ] Inventory every tRPC route, distinguishing payment-affecting vs read-only vs AI-calling
- [ ] Locate the Stripe webhook handler(s) — confirm signature verification call is present and not just a no-op. Note: subscription webhooks and Connect webhooks may be separate endpoints — both need separate verification.
- [ ] Inventory every place a Stripe key is read from env / config / secrets manager (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, plus 4 product IDs and 4 price IDs and 2 coupon IDs from `.env`)
- [ ] Inventory every place `ANTHROPIC_API_KEY` and Gemini keys are loaded — these are the AI cost-exposure vectors
- [ ] Document the **subscription lifecycle** end-to-end: signup → trial → checkout → active → tier change → cancel → past_due → terminated
- [ ] Document the **affiliate flow**: application → approval → referral code generation → click attribution → 30-day window → conversion → commission calc → Stripe Connect Express transfer
- [ ] Document the **coupon flow** — how `STRIPE_COUPON_VIP` and `STRIPE_COUPON_BEA_CREATOR` are applied (URL? admin grant? invitation code?)
- [ ] Map all tier-gated features and where each is enforced (server-side, client-side, both)
- [ ] Confirm `apps/api/src/services/` Stripe service is the *only* place Stripe SDK is called (no duplicate code paths)

**Deliverable:** Three flow diagrams (subscription, affiliate, coupon) + tier-gating matrix + Stripe surface map.

---

### Phase 2 — Automated scanning (1 day)

Same tool stack as LiveIQ audit, plus payment-specific:

| Tool | What it checks |
|---|---|
| **`reaper`** | Live validation proxy — replay payment requests with mutated amounts, currencies, recipients |
| **Semgrep** | SAST — secrets, OWASP patterns. Add Stripe-specific rules (catch raw `req.body` passed to webhook handler) |
| **gitleaks** | Scan git history specifically for Stripe live keys (`sk_live_*`, `rk_live_*`) |
| **`npm audit`** | Dependency CVEs (especially the `stripe` package version — older versions had signature verification bugs) |
| **GitHub secret scanning** | Already enabled; verify Stripe partner integration is active for early-warning |

**Deliverable:** Findings tagged by severity. Any Stripe key in git history = immediate Critical, regardless of whether it's been rotated.

---

### Phase 3 — Manual review (2-4 days)

The highest-leverage phase. Focus on what scanners can't see.

#### Stripe webhook handling — the #1 audit area
- [ ] Webhook handler uses `stripe.webhooks.constructEvent()` (or equivalent) with the raw request body, *not* a parsed JSON body
- [ ] Body parser middleware (Express `body-parser` etc.) is *not* applied to the webhook route — signature verification needs the raw bytes
- [ ] Webhook signing secret loaded from secret store, not from env file in repo
- [ ] Each webhook event has an idempotency check: `if (already_processed(event.id)) return 200` — required because Stripe retries on non-200
- [ ] Handler returns 200 quickly; expensive work goes to a queue (Stripe times out at 10s and considers slow handlers as failures, triggering retries)
- [ ] Handler does *not* trust `event.data` to determine what happened — re-fetches via `stripe.charges.retrieve()` if the event has security implications (defense in depth against signature-bypass bugs)
- [ ] Failed verifications are logged but do *not* leak whether the secret is "close" or "far off" (no error-message gradient)

#### API key handling
- [ ] No `sk_live_*` keys in any repo (including git history — check with gitleaks)
- [ ] Production uses restricted keys with least-privilege scopes, not full secret keys
- [ ] Key rotation procedure documented + tested at least once
- [ ] Separate keys per environment (dev, staging, prod); no shared keys
- [ ] Keys loaded from secrets manager (Cloudflare secrets, AWS Secrets Manager, etc.), not env files in deploys
- [ ] If LiveIQ or other services call KLING: they use service tokens, not Stripe keys directly

#### Amount integrity
- [ ] Every payout/charge amount computed server-side from authoritative data (database state, business logic), never from client input
- [ ] Currency code validated against an allowlist
- [ ] Maximum-amount safety cap enforced server-side (e.g., no single payout > $X without manual approval)
- [ ] Negative or zero amounts handled correctly (and logged as suspicious)

#### Authorization on payment-affecting endpoints
- [ ] Every "trigger payout" endpoint requires fresh authentication (re-prompt for credentials or MFA, not just session check)
- [ ] Payout destination cannot be changed by anyone other than the account owner, and the change has a cooling-off period
- [ ] Admin-only endpoints (manual refunds, force payouts, account reset) require MFA + audit log entry per action
- [ ] No "elevated session" pattern that grants admin powers via a flag set client-side
- [ ] Cross-creator IDOR tests: Creator A cannot trigger Creator B's payout via path/param tampering

#### Stripe Connect Express (affiliate payouts — confirmed in use)
- [ ] Onboarding link uses `account_links` with short expiration, single-use, tied to a session
- [ ] Each connected account is tied to exactly one affiliate in your DB; no shared accounts
- [ ] **Self-referral check** — at attribution time, verify the converting user is not the same as the affiliate (same email domain, same payment method fingerprint, same IP/device within reason)
- [ ] Commission rate (15%) is server-side constant, never read from client request
- [ ] 30-day attribution window is enforced server-side on the conversion event, not on the click event
- [ ] Referral codes are normalized (case-insensitive, trimmed) so `YOURNAME2024` and `yourname2024` don't both attribute
- [ ] Connected account capabilities are minimum needed (`transfers` only, not `card_payments`)
- [ ] Transfer creation is idempotent (same subscription period can't be paid out twice)
- [ ] Refunded subscriptions claw back the commission (otherwise affiliates can collude with users for refund-fraud)
- [ ] Connect webhook (account.updated, transfer.failed) handled separately from subscription webhook, with its own signature verification

#### Subscription billing
- [ ] Trial creation rate-limited per email + per IP + per payment method fingerprint (prevents trial farming)
- [ ] Subscription tier read from Supabase / Stripe server-side on every request — never trust a client-side `user.tier` flag
- [ ] Tier change (upgrade/downgrade) goes through Stripe, then webhook updates DB — not direct DB write from client
- [ ] Cancel-with-refund and cancel-at-period-end paths both tested
- [ ] Past-due / dunning state correctly degrades access (no Pro features for an unpaid Pro subscription)
- [ ] Subscription create webhook (`customer.subscription.created`) and tier-change webhook (`customer.subscription.updated`) both update tier atomically with the user record

#### Coupon abuse
- [ ] `STRIPE_COUPON_VIP` and `STRIPE_COUPON_BEA_CREATOR` cannot be applied via URL parameter or self-service — admin grant only OR redemption code with single-use enforcement
- [ ] Coupon application is logged with actor (admin user) and reason
- [ ] If redemption codes exist: each code is single-use, time-bound, and tied to a specific email at issue time
- [ ] No coupon stacking that produces negative subscription cost

#### Refunds / disputes / chargebacks
- [ ] Refund endpoint authorization same rigor as payout
- [ ] Dispute webhook handler updates internal state (so a disputed payout doesn't get re-triggered)
- [ ] Chargeback alerting wired up (Slack / email to the right humans)
- [ ] Refund amount cannot exceed original charge

#### Audit logging
- [ ] Every state-changing payment operation writes an immutable log entry (DB row or append-only log)
- [ ] Log includes actor (who), action (what), target (creator/account), amount, timestamp, IP, user agent
- [ ] Logs retained per regulatory requirement (7 years is a safe default for financial records)
- [ ] Logs scrubbed of secrets but *not* of identifiers — the trail must be complete

#### Tier-gating enforcement (Pro vs Director vs Trial vs VIP vs BEA Creator)
- [ ] Every Pro-only endpoint (`/analyze` video analysis, API access, white-label) checks tier server-side from current Supabase user state
- [ ] Daily AI prompt quota (10/day for Trial) enforced with a server-side counter that resets atomically — not a JS countdown
- [ ] Element library limits (100 for Director, unlimited for Pro) enforced at write time, not just at display time
- [ ] Preset library limits (25 for Director) same
- [ ] Retention policy (14/30/90 days based on tier) actually purges expired content — verify the cron / worker exists and runs
- [ ] Tier-gating is checked in tRPC middleware, not per-procedure (consistency)
- [ ] Switching tier mid-period correctly updates limits (downgrade from Pro to Director immediately re-enforces 100-element cap)
- [ ] No public tier-bypass via API access endpoint (Pro feature — paradox if a Trial user could call it)

#### AI cost abuse — Anthropic + Gemini
- [ ] `ANTHROPIC_API_KEY` and Gemini keys loaded from secrets manager, never logged
- [ ] Per-user daily token budget enforced (not just per-request) — a single user shouldn't be able to spend $X/day on AI without you knowing
- [ ] Per-user concurrent-request limit (prevents parallel-flooding within rate limit)
- [ ] 100MB video upload to `/analyze` carries the largest cost-per-call risk — confirm Pro/VIP/BEA-Creator tier check happens *before* the file uploads, not after
- [ ] Failed AI calls are retried with backoff — not infinite-loop retry on a 5xx (which could rack up cost)
- [ ] Cost monitoring + alerting wired up (Anthropic + Google Cloud billing alerts, daily spike alerts)
- [ ] If video analysis caches results: cache key is content-hash, not user-chosen filename (prevents one user paying for analysis another user can read)

#### File upload abuse (Element Library + Video Analysis)
- [ ] Server-side MIME + magic byte validation on every upload, not just extension (claimed MP4/WebM/QuickTime/AVI for video; images and PDFs separately)
- [ ] 100MB hard cap enforced server-side
- [ ] Supabase Storage bucket configured with no public listing
- [ ] Signed URLs for downloads, short expiry
- [ ] Files served from a different origin than the app (prevents stored-XSS via uploaded SVG, HTML, etc.)
- [ ] PDF uploads validated (server-side parse or pdf-magic-byte check) to prevent malicious-PDF distribution via your CDN
- [ ] Auto-expiration job (7 days, extendable) actually runs and removes files from Supabase Storage, not just DB rows (orphaned files = ongoing storage cost + retention liability)
- [ ] Per-tier storage quotas enforced before upload accepted

#### AI prompt injection (KLING-specific)
- [ ] User-supplied prompt text fed to Claude/Gemini cannot exfiltrate system prompt or other users' data
- [ ] Video analysis prompts treat the video content as untrusted input — model output is rendered as text, not parsed as instructions
- [ ] Generated Kling payloads are validated server-side against the schema in `packages/director-knowledge/schemas/` before being shown to user (defense vs prompt-injection that produces malformed payloads claiming to be legitimate)
- [ ] No tool-use capability exposed to the AI that would let it call internal APIs

#### Common payment-service bugs
- [ ] Race conditions: same payout triggered twice in parallel (DB transaction + idempotency key prevents)
- [ ] TOCTOU on payout: balance checked, then payout processed seconds later (recheck inside the transaction)
- [ ] Webhook event ordering: handler tolerates out-of-order delivery (Stripe doesn't guarantee order)
- [ ] Test mode vs live mode confusion: no test-mode keys can be used to manipulate live data

**Deliverable:** Findings doc with reproduction steps, severity, suggested fix per finding. Any Critical here is a launch-blocker.

---

### Phase 4 — Remediation (varies; budget 1-3 weeks)

- [ ] Triage: Critical/High block launch; Medium scheduled; Low/Info backlog
- [ ] Each finding gets a ticket, owner, target date
- [ ] Re-test after fix before closing
- [ ] **Special case:** any "key in git history" finding requires immediate key rotation (regardless of remediation status of the bug that allowed it)

---

### Phase 5 — Final gate (1 day)

- [ ] No Critical or High findings open
- [ ] Webhook signature verification confirmed working via deliberate-bad-signature test
- [ ] Key rotation drill completed within last 90 days
- [ ] Incident response runbook for payment incidents drafted (different from generic IR — includes Stripe support contact path, refund-pause procedure, creator-comms template)
- [ ] Disaster recovery: can you reconstruct payment state from Stripe + your audit log if your DB is lost?

**Deliverable:** Go/no-go memo.

---

## 5. `reaper` role for the KLING audit

Same proxy-record-replay-mutate pattern as the LiveIQ audit, with the KLING-specific mutation set:

**Subscription path:**
- Replay subscription webhook with valid signature but stale timestamp (idempotency check)
- Replay with tampered signature (must reject)
- Tamper with tRPC payloads that claim to set user tier (`{ tier: "pro" }` from a Trial session)
- Apply `STRIPE_COUPON_VIP` via every imaginable channel (URL param, request body, header) to confirm it's rejected outside admin grant

**Affiliate path:**
- Self-refer: sign up as affiliate with one email, sign up as user with similar email and use own referral code — confirm commission is *not* paid out
- Submit conversion with `referral_code` that doesn't exist — confirm rejected, not silently dropped
- Manipulate the attribution timestamp to extend the 30-day window
- Tamper with commission rate in any request body (must be ignored, recomputed server-side at 15%)
- Replay transfer webhook to test double-payout protection

**AI cost path:**
- Hit `/analyze` 200 times in a minute as a Trial user — confirm rate limit + tier check
- Upload 100MB video as a non-Pro user — confirm rejection happens before processing cost
- Submit a prompt-injection payload aimed at extracting the system prompt — confirm filtered

**File upload:**
- Upload `.svg` with embedded JS, renamed `.png` — confirm rejected
- Upload `.pdf` claiming to be an image — confirm rejected
- Upload 101MB file — confirm rejected at gateway, not after full upload

Most of these need ~5-10 line additions to `reaper`'s replay config. The self-referral test in particular has high payoff — it's a class of bug that's almost never caught by scanners.

---

## 6. Estimated effort

| Phase | Effort |
|---|---|
| Phase 1 Recon | 1-2 days |
| Phase 2 Automated scans | 1 day |
| Phase 3 Manual review | 4-6 days |
| Phase 4 Remediation | 2-4 weeks (depends on findings) |
| Phase 5 Final gate | 1 day |
| **Total elapsed** | **3-5 weeks** |

Revised up from v0.1's 2-4 weeks. The README revealed the surface area is broader than initially scoped: subscription billing **plus** Stripe Connect Express **plus** tier-gating **plus** AI cost exposure **plus** file uploads. Each adds its own threat surface. Higher density of Critical findings is normal for first-time SaaS+billing audits.

---

## 7. External audit recommendation

A self-audit using `reaper` + Semgrep + this checklist is appropriate for v1 launch. **Before scaling past ~$100k/month in processed payment volume, get a 3rd-party pen test from a firm with payments experience** (e.g., NCC Group, Bishop Fox, Doyensec). The third-party validation matters for:

- Future business insurance underwriting
- Larger creator partnerships requiring vendor security review
- Investor due diligence
- Genuine independent perspective (you've been staring at the code for months; they haven't)

Budget ~$15-30k for a focused payment pen test from a reputable firm. Cheaper than the cost of one undetected critical bug.

---

## 8. Open questions

Most v0.1 questions answered by the README. Remaining:

1. Is KLING-Director already processing real money (active subscriptions + affiliate payouts running), or pre-launch / soft-launch?
2. How are `STRIPE_COUPON_VIP` and `STRIPE_COUPON_BEA_CREATOR` actually granted — admin UI? Database flag? Self-applied via URL? (Determines coupon-abuse threat surface size.)
3. Bug bounty program plan post-launch?
4. Has any AI cost spike or anomalous spending event occurred? (If yes, audit prioritizes that vector higher.)
5. Is there an admin panel? If yes, it needs its own threat model (admin-only endpoints, admin role escalation).
6. Are the Anthropic + Gemini keys per-environment, or shared across dev/staging/prod?

---

## 9. Concrete next steps

1. **5-minute pre-audit smoke tests** — settle critical questions before committing the full audit:
   - Submit a bad-signature webhook to staging — confirm 400/401/403, not 200.
   - Try to apply `STRIPE_COUPON_VIP` via every URL/header/body channel as an unauth user — confirm rejected.
   - As a Trial user, set `tier: "pro"` in any request body — confirm tier is recomputed server-side.
   - Sign up as affiliate, sign up as user with same payment method, use own code — confirm conversion is flagged.
2. Run Phase 1 Recon — full surface mapping.
3. Coordinate with the LiveIQ audit if both happen in parallel — share `reaper` infra and Semgrep config.

---

## 10. Coordination with LiveIQ audit

Same engineer can run both audits sequentially (KLING first, since it's tighter and the highest-density-Critical area) OR two engineers in parallel.

Shared infrastructure:

- One `reaper` setup, two replay configs
- Shared Semgrep config (extended with payment rules for KLING)
- Shared remediation tracker
- Shared final-gate process

If running sequentially, allow 1-week gap so the team isn't context-switching between data-protection mode and payments mode mid-audit.


<a id="13-kling-director-mobile-wrapper"></a>

# 13. KLING-Director Mobile Wrapper

> Source: `docs/kling-director-mobile-wrapper-spec.md`

---

# KLING-Director Mobile Wrapper — Plan

> Working name: **kling-mobile**
> Status: Draft v0.2
> Target: iOS + Android wrapper around `KLING-Director` ([repo](https://github.com/BEA-BOLD-EVOLUTION/KLING-Director))
> Tooling lead: `full_web_converter_To_flutter_App` (forked)
> Companion to: `toklytics-liveiq-mobile-wrapper-spec.md`, `kling-director-security-audit-spec.md`

> **Confirmed scope (from README):** KLING-Director is a self-service SaaS — an AI-powered prompt compiler for Kling video generation. Users sign up via Supabase Auth, pay via Stripe subscription ($5.99 Director / $9.99 Director Pro / $0 VIP / $0 BEA Creator partner / 7-day free trial). It uses Claude Sonnet 4 + Gemini 2.0 Flash. Pro tier offers video analysis (up to 100MB uploads). It has its own affiliate program with Stripe Connect Express for 15% commission payouts. The audience is broader than LiveIQ creators — anyone can sign up.

---

## 1. Why this exists

KLING-Director is a self-service SaaS that creators and prompt engineers will use heavily from their phones (videos are watched, generated, and managed mostly on mobile). A native shell delivers three concrete wins:

1. **Push for billing + AI events** — "Trial ending in 2 days", "Video analysis complete", "Affiliate payout posted", "Subscription renewal failed". Each is high-value and time-sensitive.
2. **Native file picker for video uploads** — the `/analyze` Pro feature takes 100MB videos. The native picker (camera roll, files app) is dramatically better UX than a WebView file input.
3. **App store discoverability** — KLING-Director is a paid SaaS aimed at growth. Store listings are a real acquisition channel for "AI video tool" searches.

---

## 2. Scope

### In scope (v1)
- Native shell wrapping KLING-Director
- Biometric prompt before any money-affecting screen (not just app open)
- Native push for payment events (payout, refund, dispute, verification)
- Deep links into specific KLING screens from email / SMS
- Offline screen with explicit "payments unavailable offline" messaging
- iOS + Android distribution

### Out of scope (v1)
- Native payment UI (Apple Pay, Google Pay) — those would force you into the 30% in-app purchase tax. Stick with web/Stripe Checkout for compliance.
- Stored cards in the native shell — Stripe Checkout handles this; the app should never touch card data.
- Native UI replacement (we wrap web)
- Watch / Wear OS companions
- Tablet-optimized layouts

---

## 3. Key architectural decision: standalone, not unified

v0.1 of this spec recommended folding KLING into a unified `bea-mobile` app with LiveIQ. The README changes that calculus. **Revised recommendation: standalone `kling-mobile` app.**

### Why standalone wins here
- **Different audiences.** LiveIQ is for BEA's contracted creators. KLING-Director is a public SaaS — anyone can sign up. Most KLING users are not BEA creators. Bundling them in one app means most KLING users carry a dead LiveIQ tab they'll never use.
- **Different brand.** KLING-Director has its own product identity, pricing, affiliate program. It's a growth-channel product. LiveIQ is an agency tool. Distinct positioning calls for distinct store listings.
- **Different store category.** KLING fits "AI tools / Creativity" categories where discoverability matters; LiveIQ fits "Business / Productivity". Separate listings each rank in their best category.
- **Different update cadences.** KLING ships features rapidly (the README shows monthly improvements). LiveIQ is more stable. Coupling them slows KLING.
- **App size.** A single SaaS app loads fast. A combined app with two embedded web experiences is heavier and slower to launch.

### Cost of standalone
- Two store listings to manage (manageable — they're separate brands)
- Duplicate native infrastructure (auth shell, push token, deep-link domain) — actual code overhead is ~500 LOC, not significant
- Two install prompts — but only ever to overlapping users (BEA creators), who get a unified onboarding pitch anyway

### Decision
Standalone `kling-mobile` app, branded as "Kling Director" or similar (not "BEA Kling Director" — keep the brand clean for public market).

The LiveIQ mobile wrapper stays separate as `liveiq-mobile`.

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  FLUTTER APP — kling-mobile (single binary)                  │
│  - Native auth shell (biometric on app open + sensitive ops) │
│  - Push notification handler                                 │
│  - Deep link router                                          │
│  - WebView host (flutter_inappwebview) loading KLING web     │
│  - Native file picker bridged to WebView for /analyze upload │
└──────────────────────────────┬───────────────────────────────┘
                               │ JS bridge
                               ↓
              ┌────────────────────────────────┐
              │  KLING-Director (Next.js web)  │
              │  Hosted on Vercel              │
              │  - Detects "in Kling app" UA   │
              │  - Hides web-only chrome       │
              │  - Calls native bridge for     │
              │    upload, biometric, push     │
              └────────────────────────────────┘
```

**WebView lifecycle:**
- Single WebView, kept warm across app lifecycle
- Session cookies persist (Supabase Auth)
- Hard reload on tier-change webhook (so feature gates refresh)

**JS bridge surface:**
- `kling.registerPush()` — register FCM token with backend after sign-in
- `kling.requestBiometric(purpose)` — gated by `purpose` ("view_billing" or "manage_subscription" or "open_affiliate_dashboard")
- `kling.openExternal(url)` — opens non-app URLs in system browser
- `kling.requireFreshAuth(threshold_seconds)` — KLING calls before showing billing/payout screens
- `kling.pickFile(constraints)` — opens native file picker for `/analyze` 100MB video upload. Returns a temp URL the WebView can POST. Critical UX win.
- `kling.lockApp()` — forces re-auth on resume if anomaly detected

The `pickFile` bridge is the single biggest UX value-add over plain web — WebView file inputs are notoriously janky for large video files. Going native here is worth the 50-100 LOC.

---

## 5. Module breakdown

### 5.1 Flutter shell
- Built from `full_web_converter_To_flutter_App`
- Replace generic WebView with `flutter_inappwebview` for the JS bridge
- Add `firebase_messaging` for push
- Add `local_auth` for biometrics
- Add `app_links` for deep linking
- Add `file_picker` + `image_picker` packages for native upload picker

### 5.2 KLING-Director web app additions
- Detect UA: `Kling-Mobile/1.0`
- Apply `.in-app` CSS class to hide browser back, footer, marketing chrome
- Replace `<input type="file">` on `/analyze` with `kling.pickFile()` bridge call when in-app
- Call `kling.requireFreshAuth(...)` before rendering `/billing` and affiliate dashboard
- Expose `kling.registerPush()` after first sign-in
- Stripe Checkout: render in-app for subscription purchase; verify the redirect-back from Stripe lands on a route the WebView intercepts cleanly (this is the #1 spike risk)
- Test mode visual indicator that's prominent on mobile (banner across the top, distinct color)

### 5.3 Push notification backend
- Worker / Edge Function (likely Vercel Edge or Railway service per stack)
- Receives events from:
  - Stripe subscription webhooks → "Trial ending", "Payment failed", "Subscription renewed"
  - Stripe Connect webhooks → "Affiliate payout posted"
  - AI service callbacks → "Video analysis complete"
- Looks up user's FCM tokens (stored on sign-in)
- Sends push with deep-link target

**Push payload rules (privacy):**
- Never include dollar amounts in cleartext (lock-screen preview = info disclosure on a shared device)
- Use "Payout posted — tap to view" pattern
- Affiliate-specific events never expose other affiliates' info
- Trial-ending push lands on the billing page deep-link, not a generic URL

---

## 6. Distribution

Same as LiveIQ mobile spec, with payment-specific additions:

### iOS
- App Store guideline §3.1.1: physical goods / services *outside* the app can be paid for outside Apple's IAP. Payouts to creators (money flowing *out*) are clearly out of IAP scope — Apple won't take a cut. Document this in the submission notes.
- Privacy nutrition labels must declare financial data category
- Age rating likely 17+ stays the same

### Android
- Play Console "financial services" category may apply — verify
- Data Safety form: financial data declared

### Both
- **Stripe-specific compliance note**: if Stripe Connect is used and creator KYC happens in your app, the privacy policy needs to explicitly cover identity verification data (passport scans, etc.) and retention thereof.

---

## 7. Phased rollout

### Phase 0 — Spike (3-5 days)

Goal: Prove the WebView UX works for KLING's three trickiest paths.

- Clone fork
- Configure with KLING staging URL
- **Test 1 (most critical): Stripe Checkout subscription flow inside WebView.** Subscribe to Director tier, return to app, confirm session and tier reflected. If this breaks, fall back to opening Checkout in a Custom Tab (Android) / SFSafariViewController (iOS).
- **Test 2: Stripe Connect Express affiliate onboarding.** This is the highest-risk WebView path — Connect onboarding redirects through Stripe-hosted screens and back, and historically breaks inside WebViews. Confirm the affiliate onboard-and-return works cleanly.
- **Test 3: 100MB video upload via `/analyze`.** Use the native `kling.pickFile()` bridge. Confirm a real 90MB MP4 uploads, the analysis completes, results render. Verify the WebView doesn't OOM during upload progress.
- Side tests: biometric re-prompt timing, deep-link return paths, test-mode banner visibility.

**Decision gates:**
- Stripe Checkout works cleanly in WebView with redirect-back, OR fallback to Custom Tabs works → continue.
- Stripe Connect Express onboarding works → continue. If it breaks: design a "complete onboarding on desktop" out-of-band flow as a hard fallback.
- 100MB video upload completes without crash → continue.

If any of the three fails and has no clean fallback, this spike is the decision gate that ends the project — kling-mobile would be hampered without these flows.

---

### Phase 1 — MVP (3-4 weeks)

- [ ] Single WebView host for KLING staging then prod URL
- [ ] Kling Director brand theming (logo, splash, app icon)
- [ ] Native auth shell with biometric lock
- [ ] `requireFreshAuth` enforced on `/billing` and affiliate dashboard
- [ ] Native `pickFile` bridge for `/analyze` video upload
- [ ] FCM push for subscription + Connect + AI completion events
- [ ] Deep linking (subscription emails / referral codes)
- [ ] Offline screen
- [ ] Test/live mode visual indicator
- [ ] Stripe Checkout fallback (Custom Tabs / SFSafariViewController) if Phase 0 says needed

**Deliverable:** TestFlight + Play Internal Testing builds.

---

### Phase 2 — Store submission (2-4 weeks)

Same as LiveIQ spec, plus payment-specific submission notes.

---

### Phase 3 — Post-launch

- Add Apple Pay / Google Pay only if business case justifies the 30% tax (almost never for payouts-out)
- Add saved payment methods only if it stays compliant (Stripe Elements via webview is fine)

---

## 8. Security cross-cut

This wrapper inherits all of `kling-director-security-audit-spec.md`'s findings plus the WebView-specific items from `toklytics-liveiq-mobile-wrapper-spec.md §8`. Additionally:

- [ ] The JS bridge surface for KLING is reviewed line-by-line; nothing exposes capabilities beyond what the web origin already has
- [ ] `requireFreshAuth` cannot be bypassed by JS (the native shell decides, not the web app)
- [ ] Push notification payloads scrubbed of financial amounts
- [ ] Test mode: app shows a giant banner when running against Stripe test mode to prevent staff confusion when handling real creator support cases
- [ ] Biometric data never leaves the device (Apple/Google handle this by default, but verify your bridge code doesn't accidentally serialize biometric results)

---

## 9. Risks & open questions

| Risk | Mitigation |
|---|---|
| Stripe Checkout breaks in WebView | Phase 0 spike answers this. Fallback: Custom Tabs (Android) / SFSafariViewController (iOS). |
| Stripe Connect Express onboarding breaks in WebView | Phase 0 spike answers this. Fallback: send affiliates to a desktop-only onboarding URL via email — degraded but functional. |
| 100MB video upload OOM / crash | Use native picker + chunked upload, never load full file into WebView memory. |
| Push payload leaks info on lock screen | "Tap to view" pattern; no amounts in payload. |
| App store rejection for "minimum functionality" | Native push, biometric, file picker, deep links = enough native value to clear the bar. |
| Apple/Google scrutinize subscription apps more | Pre-built compliance: clear privacy policy, subscription terms on the listing, no dark patterns, easy cancel from in-app billing portal link. |
| Trial-ending push annoyance | Limit to one per trial, send 48 hours before expiry, allow disable from settings. |

**Open questions:**

Most prior v0.1 questions are now answered by the README. Remaining:

1. Is KLING-Director already live with active subscriptions and affiliate payouts, or pre-launch / soft-launch?
2. Is mobile launch a v1 priority, or wait until web is stable / past N MRR threshold?
3. Domain for mobile deep links — `m.kling-director.com`? Or use the existing domain with Universal Links?
4. App name on stores — "Kling Director" or branded distinctly?
5. Is there a desktop-style admin panel that wouldn't translate well to mobile? (If yes, scope it out and show a "view on desktop" message in the app for those routes.)

---

## 10. Concrete next steps

1. Phase 0 spike — 3-5 days, focused on the three critical WebView paths in §7.
2. Decision after spike — go / fall back to Custom Tabs / pivot to native-only billing screens.
3. If go: create `kling-mobile` repo (separate from `liveiq-mobile`), scaffold per §4.
4. Coordinate Phase 0 timing with the LiveIQ mobile spike — same engineer, same week, saves setup time.
5. Cross-reference the audit spec — items in §8 of this doc go into the audit's Phase 3 checklist before mobile launch.


<a id="14-spike-kit-source-files"></a>

# 14. Spike kit source files

> Working code at `bea-training-engine-spike/src/`. Listed with line counts. Full source is in the repo, not inlined here (code belongs in the repo, not a compendium).

| File | Lines | Role |
|---|---|---|
| `src/analytics_collector.py` | 202 | YouTube Analytics + drop-off-slide detection |
| `src/captions_generator.py` | 131 | deck + timing -> SRT |
| `src/module_status.py` | 321 | Editorial review state machine |
| `src/notebooklm_client.py` | 316 | NotebookLM Enterprise REST client |
| `src/slide_deriver.py` | 166 | Claude: psychology analysis + typed deck |
| `src/spike_orchestrator.py` | 723 | CLI; every pipeline step command |
| `src/thumbnail_generator.py` | 279 | PIL / tRPC-text / tRPC-url backends |
| `src/translator.py` | 163 | Cloud Translation, glossary-protected |
| `src/tts_client.py` | 97 | Kokoro / Google Cloud TTS, language-aware |
| `src/video_renderer.py` | 231 | PIL slides + ffmpeg (Phase 0; Remotion replaces in Phase 1) |
| `src/youtube_auth.py` | 99 | OAuth setup + credential loader |
| `src/youtube_publisher.py` | 266 | videos.insert + thumbnail + captions + playlist |

## Prompt templates

| File | Role |
|---|---|
| `prompts/slide-outline.md` | Psychology analysis + typed slide outline prompt |
| `prompts/narration.md` | Per-kind tone + pacing prompt |

## Other kit files

- `README.md` — how to run the spike
- `setup.sh` — clone forks + bootstrap venv + tool checks
- `.env.example` — all config knobs documented inline
- `brand/theme.json` — brand tokens + per-language voice map
- `evaluation/decision-memo-template.md` + `evaluation/rubric.md` — Day 3 gate

---

*End of compendium. Source of truth: `docs/` + `bea-training-engine-spike/` on branch `claude/setup-repo-execution-dXbhZ`.*
