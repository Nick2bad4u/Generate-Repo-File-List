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
