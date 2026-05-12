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

## How a module is structured

Every module = a sequence of typed scenes from this fixed vocabulary. The deck.json schema (see Remotion architecture doc) has a `kind` field per slide drawn from this list:

| Kind | Purpose | Where it lives |
|---|---|---|
| `hook` | First 3-5 seconds. A scene the creator instantly recognizes from their own LIVEs. No "welcome." | Slide 1 only |
| `what` | One-sentence definition of the concept being taught. | After hook |
| `why` | Emotional + practical reason this matters. Ties to money / growth / visibility / loyalty / confidence / consistency. | After what |
| `how` | Numbered or bulleted step-by-step action. | Core teaching slides |
| `script` | Exact words/phrases to use during LIVE. Fillable templates. | When applicable |
| `mistake` | Common failure pattern with the correct alternative. | Mid-module |
| `success` | What "doing it right" looks like, with a concrete metric. | After how/mistake |
| `recap` | Question that forces retrieval ("What did we just learn?"). | Periodically |
| `identity` | One line reinforcing professional creator identity. | Inserted naturally |
| `action` | "Do this immediately." Specific, time-bound. | Closing |
| `reflection` | Open question for the creator to sit with. | Closing |
| `checkpoint` | Measurable target to track over N days. | Closing |

A 90-second module typically uses 6-9 scenes. A 3-minute module uses 12-18. The closing trio (action / reflection / checkpoint) is non-optional.

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

A 90-second module on "Acknowledging gifters within 8 seconds":

| Time | Scene kind | What's on screen + spoken |
|---|---|---|
| 0:00-0:05 | `hook` | A Lion just dropped in your LIVE. Chat is exploding. You have 8 seconds. |
| 0:05-0:15 | `what` | "Acknowledge fast" means name the gifter + name the gift within 8 seconds of landing. |
| 0:15-0:30 | `why` | Top creators who acknowledge in <8s see 3x higher repeat-gift rate. The gifter feels seen — that's the entire emotional contract of a LIVE. |
| 0:30-0:55 | `how` | Three steps: (1) stop your sentence. (2) say their @handle + gift name. (3) one specific thank-you, not a generic "thanks." |
| 0:55-1:10 | `script` | "Yo [@username] — that Lion. Thank you. You just made tonight." |
| 1:10-1:20 | `mistake` | Don't say "thanks for the gifts" when one specific person dropped it. They tune out. |
| 1:20-1:30 | `success` | You're hitting the bar if 80%+ of your top-3 gifters return within the next week. |
| 1:30-1:35 | `recap` | What's the 8-second rule? |
| 1:35-1:45 | `action` | On your next LIVE: set a mental timer the second you see a top gift. Force yourself to name + thank within 8 seconds. |
| 1:45-1:50 | `reflection` | Which gifters made you feel seen last week? What did they say? |
| 1:50-1:55 | `checkpoint` | Track this for 7 LIVEs: how often did you acknowledge within 8 seconds? |

That's the standard. Every module hits that bar or doesn't ship.

---

## Where this doc gets consumed

- `prompts/slide-outline.md` — references this doc by name and inherits the structure
- `prompts/narration.md` — references this doc for tone + closing-trio rules
- `docs/bea-training-engine-remotion-architecture.md` — typed-slide vocabulary maps 1:1 to Remotion components
- `bea-training-engine-spike/src/module_status.py` — editorial review checklist includes pedagogy compliance items
- `docs/bea-training-engine-quality-strategy.md` — references this doc as content-quality bar (alongside the production-quality bar)

If you change something here, all of the above need to track the change.
