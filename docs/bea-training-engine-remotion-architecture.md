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
