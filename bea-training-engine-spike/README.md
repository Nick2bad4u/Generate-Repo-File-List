# BEA Training Engine — Phase 0 Spike Kit

This directory is the **starter kit** for the BEA Training Engine Phase 0 spike, as defined in `../docs/bea-training-engine-spike-runbook.md`. It contains the scaffolding, setup scripts, prompt templates, and evaluation form needed to execute the 3-day spike.

**This kit is repo-portable.** When you're ready, `git mv bea-training-engine-spike/* ../bea-training-engine/` into a new dedicated repo (or just `mv` the directory and `git init` from inside it).

---

## What this is — and isn't

**This is:**
- A spike harness: setup + skeleton + prompts + evaluation form
- Enough to start Day 1 of the runbook in ~15 minutes after `setup.sh` completes
- Framework-agnostic where it can be (prompts, eval form) and explicit-TODO where it can't (API integration)

**This isn't:**
- A working end-to-end pipeline — that's what the spike *proves out*
- Production code — corners are cut intentionally for speed
- Final architecture — see `../docs/bea-training-engine-spec.md` for Phase 1+

---

## Prerequisites

- Python 3.11+
- Git
- **Google Cloud project with NotebookLM Enterprise license enabled** ([setup docs](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks))
- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- An Anthropic API key (Claude does the slide derivation)
- BEA brand assets (logo PNG, brand colors, fonts) — see `brand/README.md`
- 1-3 BEA source documents on the spike topic (Markdown or PDF)
- The spike topic chosen: default is **"How to acknowledge a gifter on TikTok LIVE"**

> **Note on Enterprise license:** The official NotebookLM API is in Preview and requires a NotebookLM Enterprise license on your Google Cloud project. If you don't have it yet, the kit supports a fallback path using the unofficial `notebooklm-py` fork — set `USE_LEGACY_NOTEBOOKLM=true` before running `setup.sh`. Either way, treat the Enterprise API as the production target.

---

## 15-minute setup

```bash
# 1. Authenticate gcloud (if you haven't already)
gcloud auth login
gcloud auth application-default login

# 2. From this directory
./setup.sh

# 3. Copy and fill in env vars
cp .env.example .env
# Edit .env: GCP_PROJECT_NUMBER, NOTEBOOKLM_LOCATION, ANTHROPIC_API_KEY

# 4. Activate the Python venv
source .venv/bin/activate

# 5. Place your source docs in inputs/
cp /path/to/your/bea-docs/*.{md,pdf} inputs/

# 6. Fill in brand/theme.json + drop logo.png
#    See brand/README.md
```

---

## The three spike days

Each day's tasks come straight from the runbook. The orchestrator (`src/spike_orchestrator.py`) walks through the official NotebookLM Enterprise API + Claude flow.

### Day 1 — Setup, notebook, sources, kick audio overview

```bash
python src/spike_orchestrator.py auth
python src/spike_orchestrator.py create-notebook --title "BEA Training Spike"
python src/spike_orchestrator.py upload-sources --inputs inputs/
python src/spike_orchestrator.py kick-audio-overview \
    --topic "How to acknowledge a gifter on TikTok LIVE"
```

End-of-day deliverable: notebook created with sources, audio overview generation kicked off (it takes a few minutes). The CRITICAL Day 1 verification: confirm we can actually retrieve the audio + transcript via API. See the runbook for fallback paths if not.

### Day 2 — Fetch overview, derive deck via Claude, render video

```bash
python src/spike_orchestrator.py fetch-audio-overview
# inspect outputs/01-audio-overview.json carefully
python src/spike_orchestrator.py derive-deck \
    --topic "How to acknowledge a gifter on TikTok LIVE"
python src/spike_orchestrator.py render-video \
    --deck outputs/01-deck-spike/deck.json
```

End-of-day deliverable: `outputs/01-video-spike.mp4`.

### Day 2.5 — Captions + YouTube publish (Phase 1 preview)

The spike includes working modules for the back half of the pipeline:

```bash
# One-time per machine: OAuth consent for the @boldevolution channel
# (download client secret JSON to secrets/youtube-client-secret.json first)
python src/youtube_auth.py

# Generate SRT captions from the deck + render timings
python src/spike_orchestrator.py generate-captions

# Upload MP4 + captions + (optional) thumbnail to YouTube as unlisted
python src/spike_orchestrator.py publish-youtube

# Once views accumulate, pull analytics + per-slide drop-off insights
python src/spike_orchestrator.py fetch-analytics --video-id <YouTube ID>
```

### Day 3 — Evaluate + decide

```bash
cp evaluation/decision-memo-template.md evaluation/decision-memo.md
$EDITOR evaluation/decision-memo.md
```

End-of-day deliverable: filled `evaluation/decision-memo.md` + recommendation (go / tune / pivot).

---

## Directory layout

```
bea-training-engine-spike/
├── README.md                         # this file
├── setup.sh                          # clone forks + bootstrap venv
├── .env.example                      # env vars to set
├── requirements.txt                  # Python deps
├── src/
│   ├── spike_orchestrator.py         # CLI; all step commands
│   ├── notebooklm_client.py          # NotebookLM Enterprise REST client
│   ├── slide_deriver.py              # Claude → deck.json
│   ├── tts_client.py                 # Kokoro (default) / Google Cloud TTS
│   ├── video_renderer.py             # PIL slides + ffmpeg → MP4 + timing.json
│   ├── captions_generator.py         # deck + timing → SRT
│   ├── youtube_auth.py               # OAuth setup + credentials loader
│   ├── youtube_publisher.py          # videos.insert + thumbnails.set + captions.insert
│   └── analytics_collector.py        # YouTube Analytics + drop-off slide detection
├── prompts/
│   ├── slide-outline.md              # template for slide deck generation
│   ├── narration.md                  # template for narration script
│   └── README.md                     # how to iterate on prompts
├── brand/
│   ├── theme.json                    # brand config (brand_name + youtube_channel locked)
│   └── README.md                     # what to populate
├── secrets/                          # gitignored — OAuth artifacts live here
├── inputs/                           # gitignored — place source docs here
├── outputs/                          # gitignored — spike artifacts land here
└── evaluation/
    ├── decision-memo-template.md     # fillable form for Day 3
    └── rubric.md                     # the scoring rubric from the runbook
```

---

## How to migrate this to a real repo

When the spike succeeds and you're ready to start Phase 1:

```bash
# Option A: just move the whole directory
mv bea-training-engine-spike/ /path/to/new/bea-training-engine
cd /path/to/new/bea-training-engine
git init
gh repo create BEA-BOLD-EVOLUTION/bea-training-engine --private --source=. --push

# Option B: move just the salvageable parts
# - keep: prompts/, brand/, evaluation/decision-memo.md (now filled in)
# - drop: src/ (Phase 1 rewrites it)
# - replace README with Phase 1 README
```

---

## When to abandon the spike

Per runbook §1, a "no-go" decision is *valuable output*. Stop early if:

- Day 1: NotebookLM auth via `notebooklm-py` is unreliable or violates ToS terms in a way that worries you
- Day 2: The video render quality is so far below ship-quality that fixing it would require building a new pipeline
- Day 2: `training-video-generator` requires manual steps that can't be automated

Document the failure in `evaluation/decision-memo.md` and propose alternatives (Synthesia, HeyGen, Remotion). A clean "no" with reasoning is the right deliverable.

---

## Cross-references

| Doc | Location |
|---|---|
| Full design spec | `../docs/bea-training-engine-spec.md` |
| Detailed runbook | `../docs/bea-training-engine-spike-runbook.md` |
| **NotebookLM Enterprise API** (primary) | https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks |
| Fork: Training Video Generator | https://github.com/BEA-BOLD-EVOLUTION/training-video-generator |
| Fork: notebooklm-py (legacy fallback only) | https://github.com/BEA-BOLD-EVOLUTION/notebooklm-py |
