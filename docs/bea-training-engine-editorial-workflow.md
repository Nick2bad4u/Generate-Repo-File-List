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
- [ ] Slide 1 is a `hook` — recognizable scene, no "welcome"
- [ ] Module answers all 5 questions: What / Why / How / Success / Mistakes
- [ ] Closing trio present in order: `action` → `reflection` → `checkpoint`
- [ ] Every `why` slide ties to money / growth / visibility / loyalty / confidence / consistency
- [ ] Every `checkpoint` includes a quantified metric + duration
- [ ] No corporate filler ("in this video", "it's important to note", "studies have shown")
- [ ] Pattern variety — no 3+ same `kind` slides in a row
- [ ] Length matches target ±10%

Modules failing any of the above are rejected with reason `pedagogy` (not `factual` or `off-topic`). The rejection feedback loop in `slide_deriver.py` reads the specific pedagogy failure and adjusts the next generation pass.

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
