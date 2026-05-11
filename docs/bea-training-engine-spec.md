# BEA Training Engine — Design Spec

> Working name: **bea-training-engine**
> Status: Draft v0.1
> Owner: Bold Evolution Agency

---

## 1. Vision

A pipeline that turns BEA's accumulated creator knowledge into **personalized training videos**, automatically — for use in the LMS, creator portals, and as direct creator coaching deliverables.

Topic in (or creator profile in) → finished MP4 + thumbnail + LMS module out, with minimal human authoring per video.

The engine leverages the NotebookLM ecosystem forks already in the BEA-BOLD-EVOLUTION account, combined with Claude orchestration and BEA's own knowledge base.

---

## 2. Success criteria

| Metric | Target |
|---|---|
| Time from topic → published video | < 15 min unattended |
| Cost per finished video | < $5 in API/compute |
| Per-creator personalization | At least 3 data points from creator's last 30 days injected into script |
| Reuse rate | One source module produces ≥ 5 variants (regional, level, language) |
| Quality bar | A creator can't tell it from a hand-authored video on first watch |

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
2. Is per-creator personalization the v1 differentiator or a v2 unlock?
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
