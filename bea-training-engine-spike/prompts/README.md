# Prompts

Curated prompt templates used by the spike orchestrator. Each template is its own markdown file so they're easy to edit, diff, version-control, and A/B test.

## Inventory

| File | Used by | Purpose |
|---|---|---|
| `slide-outline.md` | `generate-deck` | Turn a topic + source corpus into a slide outline |
| `narration.md` | `generate-deck` | Expand each slide into spoken narration |

## Iterating during the spike

If a slide deck or narration comes out weak:

1. Don't change the orchestrator code — change the prompt.
2. Commit each meaningful prompt change with a one-line note on what was wrong with the prior output.
3. Keep a `prompts/notes.md` (gitignored or tracked, your call) with what you tried and what improved.

The prompt library is the highest-leverage thing in this spike. Most quality issues are prompt issues, not code issues.

## After the spike

If Phase 1 proceeds, these prompts move to the new repo at `prompts/` as-is. They are the bridge between the spike and Phase 1 — most other code gets rewritten.
