# BEA Training Engine — Phase 0 Spike Runbook

> Time-box: **3 days**
> Goal: Produce **one watchable BEA-branded training video** end-to-end from a fixed topic, with no orchestration / personalization / automation.
> Output: Decision memo on whether `training-video-generator` quality is acceptable as-is, or needs significant rework before Phase 1.

> **v0.2 update:** Pivoted from the unofficial `notebooklm-py` fork to the official **NotebookLM Enterprise REST API** (Google Cloud, Preview / v1alpha). Key implications:
> - Auth via `gcloud auth print-access-token`, not session cookies
> - Requires a NotebookLM Enterprise license on your GCP project
> - The Enterprise API exposes notebooks + sources + audio overviews; **slide-deck generation is not a documented output** — Claude derives slides from the audio overview transcript + source corpus
> - Day 1's critical verification is: *can we actually retrieve the audio file and transcript via API?* If not, see §"Day 1 blocker paths" below.

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
| Sources endpoint not findable | **Path B** | Skip NotebookLM entirely. Use Claude with the source corpus + `prompts/slide-outline.md` to produce the deck directly. Lose the audio-overview voice; gain immediate progress. |
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
