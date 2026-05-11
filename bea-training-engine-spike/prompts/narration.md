# Narration Prompt

> Used by `spike_orchestrator.py generate-deck` (or NotebookLM directly) to expand each slide into spoken narration.

---

You are writing narration for a short BEA training video for TikTok LIVE creators. The slide outline has already been produced; your job is to write the exact words a voice actor (or TTS engine) will speak for each slide.

## Inputs you'll receive

- The full slide outline (JSON)
- The source corpus from the NotebookLM notebook
- Target total length in seconds

## Per-slide narration constraints

| Constraint | Value |
|---|---|
| Pacing | ~155 words per minute (natural conversational rate) |
| Tone | Warm, direct, like a coach mid-LIVE — not formal |
| First-person we | "When we acknowledge..." not "When creators acknowledge..." |
| Sentence length | Mostly short. Mix in one longer sentence per slide for rhythm. |
| Filler words | None. Cut "really", "very", "basically", "actually". |
| Reading aloud | If a sentence sounds weird spoken, rewrite it. |

## Slide-specific guidance

- **Opening slide** (~10s): a scene the creator instantly recognizes. Skip pleasantries. No "Hi creators, today we'll be discussing..."
- **Teaching slides** (~10-15s each): One concrete thing. Action verb up front. End with a moment of resolution ("...and you've kept them in the room.").
- **Closing slide** (~10s): One sentence the creator can repeat to themselves before their next LIVE. Memorable. No "thank you for watching."

## Voice / language patterns to use

- Direct address: "you", "your", "your gifter"
- Specifics over abstractions: "a Lion gift is 29,999 coins" > "a high-value gift"
- Concrete time intervals: "within 8 seconds" > "promptly"
- Named patterns from the source corpus, cited inline if helpful

## Voice / language patterns to avoid

- "In conclusion"
- "It's worth noting that"
- "Studies have shown" (unless you cite the BEA source)
- Hedge words: "might", "could potentially", "may want to consider"

## Output format

Return strict JSON, one entry per slide:

```json
{
  "narration": [
    {
      "slide_index": 1,
      "text": "<the exact words to speak>",
      "estimated_seconds": <int>,
      "emphasis_words": ["<word>", "<word>"]
    }
  ]
}
```

`emphasis_words` is an optional hint to the TTS engine; the renderer can ignore it for the spike.

## Final check before returning

Read the narration aloud. If you stumble, rewrite. If it sounds like a corporate training video voiceover, rewrite. If a creator wouldn't say it on their own LIVE, rewrite.
