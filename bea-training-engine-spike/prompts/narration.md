# Narration Prompt

> Used by `spike_orchestrator.py derive-deck` (combined with `slide-outline.md`) to produce the exact spoken words per slide.
>
> **This prompt enforces the BEA pedagogy.** See `docs/bea-training-engine-pedagogy.md`.

---

You are writing narration for a BEA training video aimed at TikTok LIVE creators. The slide outline (with typed `kind` per slide) is already produced. Your job: write the exact words a TTS voice will speak per slide.

## Audience reminder

Adults 18-50, mobile-first, ADHD-friendly, social-media conditioned. Many learn by doing. Many are overwhelmed. They are NOT consuming this in a classroom — they're watching it on their phone between LIVEs.

## Per-slide narration rules

| Rule | Why |
|---|---|
| Pacing ~155 words/minute | Natural conversational rate |
| Mix sentence length | Mostly short. One longer sentence per slide for rhythm. |
| Direct address: "you", "your" | This is for the creator, not "creators in general" |
| First-person plural sparingly | "When we acknowledge…" is fine. "We will explore…" is not. |
| No filler | Cut: really, very, basically, actually, in conclusion, it's important to note |
| No hedge words | Cut: might, could potentially, may want to consider. State it. |
| Read aloud test | If a sentence sounds weird spoken, rewrite. |

## Tone targets per `kind`

Different slide kinds demand different tones inside the same module. Match the tone to the slide's job:

| `kind` | Tone | Pacing |
|---|---|---|
| `hook` | Punchy, scene-specific, in-the-moment | Fast, ~6 seconds for a typical hook |
| `what` | Crisp, definitional | Slower, deliberate — let the definition land |
| `why` | Emotionally weighted | Mid-pace; emphasize the stakes |
| `how` | Procedural, sequential | Steady; one step lands before the next starts |
| `script` | Demonstrative — actually perform the line | Slow + clear so creators can copy |
| `mistake` | Slightly cautionary, never preachy | Mid-pace; the consequence carries weight |
| `success` | Concrete, confident | Mid-pace; numbers should land clearly |
| `recap` | Conversational question + pause | Pause after the question (use an ellipsis to signal it) |
| `identity` | Affirming, not flattering | Slow, only one sentence |
| `action` | Command, direct | Fast and crisp — this is the "go" |
| `reflection` | Slowed down, intimate | Slowest pacing in the module |
| `checkpoint` | Practical, measurable | Mid-pace; the number is the point |

## Behavior-driven framing

For every `why`, `success`, and `checkpoint` slide, the narration must explicitly tie to one of:

- Money (gifts, payouts, revenue)
- Growth (viewer count, FYP)
- Visibility (algorithm signal, recommended feed)
- Audience loyalty (return rate, repeat gifters)
- Confidence (creator's own emotional state)
- Consistency (showing up reliably)

Pick the most relevant for the specific slide. Make the tie explicit, not implied.

## Identity reinforcement

Sparingly — at most one explicit identity line per module — drop a phrase like:

- "This is what pro creators do."
- "Treating this as a craft — that's the difference."
- "You're not winging it anymore. You're building a system."

Don't overdo it. One landing well > five generic ones.

## Anti-patterns (rewrite if you see these)

- "In this video we will discuss…"
- "Welcome back creators…"
- "It's worth noting that…"
- "There are several factors to consider…"
- "Studies have shown…" (unless you cite a specific BEA source)
- "Without further ado…"
- Listicles longer than 3 items spoken aloud (split into separate slides)

## Closing trio narration — special rules

The last three slides (`action`, `reflection`, `checkpoint`) are the conversion point of the entire module. They get special treatment:

- **`action`**: command form. "Do this." "On your next LIVE, …" No softeners ("you might want to"). The creator should know exactly what to do in the next 24 hours.
- **`reflection`**: spoken slowly. Use the second person ("Which gifters made *you* feel seen?"). Don't answer the question — let it sit.
- **`checkpoint`**: state the metric and the duration plainly. "Track this for 7 LIVEs: how often did you acknowledge within 8 seconds?"

If any of the closing three feel generic, rewrite them. They are the most important slides in the module.

## Output format — strict JSON

```json
{
  "narration": [
    {
      "slide_index": 1,
      "text": "<exact words to speak>",
      "estimated_seconds": <int>,
      "emphasis_words": ["<word>", "<word>"]
    }
  ]
}
```

`emphasis_words` is a list of words the TTS engine should stress (renderer can choose to honor or ignore).

## Final check

Read each slide's narration aloud at conversational pace. Time it against the slide's `estimated_seconds`. If it's more than 20% off, rewrite. If it sounds like a corporate training voiceover, rewrite. If the closing trio doesn't make you want to actually do something, rewrite.
