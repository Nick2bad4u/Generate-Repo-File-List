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
- A Google account with NotebookLM access
- BEA brand assets (logo PNG, brand colors, fonts) — see `brand/README.md`
- 1-3 BEA source documents on the spike topic (Markdown or PDF)
- The spike topic chosen: default is **"How to acknowledge a gifter on TikTok LIVE"**

---

## 15-minute setup

```bash
# 1. From this directory
./setup.sh

# 2. Copy and fill in env vars
cp .env.example .env
# Edit .env with your Anthropic key (for orchestration) and any NotebookLM creds

# 3. Activate the Python venv
source .venv/bin/activate

# 4. Place your source docs in inputs/
mkdir -p inputs && cp /path/to/your/bea-docs/*.{md,pdf} inputs/

# 5. Place brand assets
# See brand/README.md
```

---

## The three spike days

Each day's tasks come straight from the runbook. The orchestrator skeleton (`src/spike_orchestrator.py`) gives you the structure; you fill in the API specifics after reading `notebooklm-py/README.md` and `training-video-generator/README.md`.

### Day 1 — Setup + first NotebookLM call

```bash
python src/spike_orchestrator.py auth
python src/spike_orchestrator.py upload --inputs inputs/
python src/spike_orchestrator.py test-generate
```

End-of-day deliverable: programmatic output from NotebookLM about your source docs.

### Day 2 — Slides + script + video

```bash
python src/spike_orchestrator.py generate-deck --topic "How to acknowledge a gifter on TikTok LIVE"
python src/spike_orchestrator.py render-video --deck outputs/01-deck-spike/deck.json
```

End-of-day deliverable: `outputs/01-video-spike.mp4`.

### Day 3 — Evaluate + decide

```bash
# Open the decision memo template
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
│   ├── spike_orchestrator.py         # CLI with day-1 / day-2 commands
│   ├── notebooklm_client.py          # thin wrapper, TODOs to fill in
│   └── video_renderer.py             # thin wrapper, TODOs to fill in
├── prompts/
│   ├── slide-outline.md              # template for slide deck generation
│   ├── narration.md                  # template for narration script
│   └── README.md                     # how to iterate on prompts
├── brand/
│   ├── theme.json                    # BEA brand config (PLACEHOLDER — fill in)
│   └── README.md                     # what to populate
├── inputs/                           # gitignored — place source docs here
│   └── .gitkeep
├── outputs/                          # gitignored — spike artifacts land here
│   └── .gitkeep
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
| Fork: NotebookLM Python API | https://github.com/BEA-BOLD-EVOLUTION/notebooklm-py |
| Fork: Training Video Generator | https://github.com/BEA-BOLD-EVOLUTION/training-video-generator |
