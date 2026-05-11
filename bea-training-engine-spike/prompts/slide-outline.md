# Slide Outline Prompt

> Used by `spike_orchestrator.py generate-deck` to produce a slide outline grounded in the uploaded BEA source documents.

---

You are designing a short training video for a TikTok LIVE creator working with Bold Evolution Agency (BEA). The audience is creators who already know the basics of TikTok LIVE and want practical, immediately-applicable coaching.

## Inputs you'll receive

- **Topic:** the subject of this training (e.g., "How to acknowledge a gifter on TikTok LIVE")
- **Source corpus:** uploaded BEA documents (Live Guide, LMS modules, top-creator transcripts, compliance notes)
- **Constraints:** target video length in seconds, target slide count

## Your task

Produce a slide outline that:

1. **Stays inside the source corpus.** Do not invent BEA-specific advice that isn't in the uploaded documents. If a claim can't be cited, drop it. Generic platform advice is fine if labeled as such.
2. **Opens with a creator's pain.** The first slide should land on a specific moment a creator recognizes from their own LIVEs ("You just got a Lion. The chat is exploding. What now?"). No "Welcome to this training" openings.
3. **Each middle slide teaches one thing.** One action, one decision rule, one phrasing pattern. Not three. If a slide has more than one teaching point, split it.
4. **Closes with a one-line takeaway.** Something the creator can practice on their next LIVE without rewatching.
5. **Cites sources inline.** Each slide should reference which source document(s) informed it, by filename or section.

## Output format

Return strict JSON in this shape:

```json
{
  "topic": "<the topic>",
  "target_seconds": <int>,
  "narration_style": "warm, direct, specific — like a coach who's done 1000 LIVEs",
  "slides": [
    {
      "index": 1,
      "title": "<5-7 words, action-oriented>",
      "bullets": ["<short bullet>", "<short bullet>"],
      "speaker_intent": "<what this slide is supposed to accomplish in one sentence>",
      "sources": ["<filename or section ref>"]
    }
  ]
}
```

## Style constraints

- Avoid generic AI/training language: "in this section", "we will explore", "best practices include"
- No emojis in titles or bullets
- Use creator vocabulary (gift, battle, gifter, LFG, FYP) — assume domain fluency
- Numbers and named tactics > vague principles ("Acknowledge within 8 seconds" > "Acknowledge quickly")

## Anti-patterns to avoid

- "There are several factors to consider..."
- "It's important to remember that..."
- Listicles longer than 3 items per slide
- Closing slides that are just "Thanks for watching"
