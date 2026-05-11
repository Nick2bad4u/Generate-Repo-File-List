# BEA Training Engine — Phase 0 Spike Runbook

> Time-box: **3 days**
> Goal: Produce **one watchable BEA-branded training video** end-to-end from a fixed topic, with no orchestration / personalization / automation.
> Output: Decision memo on whether `training-video-generator` quality is acceptable as-is, or needs significant rework before Phase 1.

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
| Google account with NotebookLM access | ⬜ | Personal or workspace |
| Cloud NotebookLM is acceptable for spike content | ⬜ | Use generic topic, no creator data |
| Local Python 3.11+ environment | ⬜ | |
| 1 BEA branding asset bundle | ⬜ | Logo PNG, brand colors hex, intro music if used |
| 1 fixed sample topic chosen | ⬜ | Recommend: *"How to acknowledge a gifter on TikTok LIVE"* — short, well-trodden, easy to evaluate quality |
| 1-3 source documents on the topic | ⬜ | Pull from BEA-Live-Guide; PDF/Markdown is fine |

---

## Day 1 — Setup & first NotebookLM run

### Morning: environment

```bash
# Working directory for the spike
mkdir -p ~/spikes/bea-training-engine && cd ~/spikes/bea-training-engine

# Clone the two key forks
git clone https://github.com/BEA-BOLD-EVOLUTION/notebooklm-py.git
git clone https://github.com/BEA-BOLD-EVOLUTION/training-video-generator.git

# Python env
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ./notebooklm-py
pip install -r ./training-video-generator/requirements.txt
```

### Afternoon: NotebookLM auth & first call

1. Read `notebooklm-py/README.md` end to end. Note the auth method (browser cookies, OAuth, or session token).
2. Authenticate per its instructions.
3. Create a new NotebookLM notebook manually in the web UI; upload the 1-3 BEA source docs.
4. Run the `notebooklm-py` "list notebooks" example to confirm API access works.
5. Run a "generate audio overview" or "generate study guide" call (whichever the API exposes most cleanly).

**End of Day 1 success criterion:** You can programmatically get *some* output from NotebookLM about the BEA source docs.

**If blocked:** the most likely failure is auth. Document the failure mode and stop — this is a signal that `notebooklm-py` may not be reliable enough for the engine. Decision gate triggered early.

---

## Day 2 — Slides + script generation, video render

### Morning: slide deck + narration

1. Identify which `notebooklm-py` endpoint produces something close to a slide outline or video script. (May need to combine: audio overview → transcript → outline.)
2. Generate the artifacts for the chosen topic.
3. Save outputs to `outputs/01-deck-spike/`:
   - `slides.json` or `slides.md` — slide content
   - `narration.txt` — what's spoken per slide
   - `sources.md` — what NotebookLM cited

**Sanity check before continuing:** Read the script aloud. Does it sound like BEA, or like generic AI mush? Note your gut reaction — this is data for the decision memo.

### Afternoon: video render

1. Read `training-video-generator/README.md`. Understand its expected input format.
2. Adapt the Day 2 morning outputs to its expected format. Likely needs:
   - Slide images or markdown
   - Narration text per slide (or per timestamp)
   - Brand config (logo path, color palette)
3. Run the generator end-to-end.
4. Save the resulting MP4 to `outputs/01-video-spike.mp4`.

**End of Day 2 success criterion:** You have a playable MP4 file.

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
