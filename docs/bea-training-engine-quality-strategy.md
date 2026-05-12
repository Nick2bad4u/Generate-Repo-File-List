# BEA Training Engine — Quality Strategy

> The north-star quality vision and the ladder that every spike, sprint, and decision must climb. Anchor doc — if a piece of work isn't moving us toward the end state defined here, it's the wrong work.

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
| 1 | **Voice** (Kokoro → ElevenLabs voice clone) | 1 day | Massive — biggest perceived-quality lever | $0.30/video |
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
- Swap Kokoro for ElevenLabs (or commit to a different premium voice provider)
- Voice-clone a consistent BEA brand voice OR pick a flagship voice and stick with it across all modules
- Tune narration prompt for natural conversational tone, not slide-readout cadence

**Gate:** play a generated video for a creator-volunteer (someone in the BEA network, not the team). They cannot tell within 30 seconds that the voice is AI-generated, OR they can tell and don't care because the content is engaging.

**Why this phase before the bigger Phase 1:** voice is the single biggest perceived-quality lever and it's a one-day swap. Hitting Phase 0.5's gate validates that the *content* generation is good enough that voice was the bottleneck. If creators reject even with a good voice, the problem is content / structure / pacing — and that's a different fix than visual production.

**Status:** not started.

---

### Phase 1 — Visual production floor

**Goal:** move from slideshow to actual video.
**Specific work:**
- Replace PIL slide renderer with Remotion (or equivalent programmatic video framework)
- Build 3-5 reusable templates (intro, teaching slide, demonstration frame, callout, outro)
- Wire stock b-roll API (Pexels or Storyblocks) — Claude derives search queries per slide
- Add music bed (Epidemic Sound) with auto-ducking under narration
- Add stylized caption / lower-third overlay
- Implement first-5-seconds hook structure in the prompt

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

1. **Voice provider:** ElevenLabs (premium AI), real human voiceover (Fiverr Pro / hired VO), or a hybrid (real VO for flagship, ElevenLabs for standard)?
2. **Visual framework:** Remotion (React, TypeScript), Manim (Python, math-focused), After Effects automation (Adobe), or a SaaS like Pictory?
3. **Stock footage budget:** Pexels free, Storyblocks ~$30/mo, or Artgrid ~$300/yr per seat?
4. **Brand voice consistency:** clone a real BEA team member's voice, or pick a pro voice and own it as the BEA voice?
5. **Flagship cadence:** how many Premium-tier modules per quarter? Drives the human-producer budget.

These don't need answers today but should be answered before Phase 0.5 starts.
