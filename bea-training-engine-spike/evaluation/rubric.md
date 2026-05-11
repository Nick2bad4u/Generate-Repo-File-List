# Spike Evaluation Rubric

> Reference for what each score means on the decision memo's 1-5 scale.

| Score | Meaning |
|---|---|
| **5** | Ship-quality as-is. Could publish today. |
| **4** | Almost ship-quality. One or two small polish items away. |
| **3** | Watchable. Needs work but the bones are right. |
| **2** | Not watchable as-is. Significant rework needed. |
| **1** | Unusable. Wrong stack or wrong approach. |

## Per-dimension definitions

### Visual polish
- **5**: Indistinguishable from a designed-by-hand BEA video
- **3**: Recognizably BEA-branded but with awkward layout/spacing/transitions
- **1**: Generic AI-video aesthetic; doesn't say "BEA" at all

### Narration quality
- **5**: Sounds like a coach. Natural pacing, right pronunciations, emotional engagement.
- **3**: Functionally listenable; some awkward phrasing or mispronunciations (e.g., "TikTok" said wrong) but creators would still get value
- **1**: TTS-uncanny-valley. Would lose creators in the first 10 seconds.

### Script accuracy
- **5**: Every claim traces to a BEA source doc. No fabrication.
- **3**: Mostly accurate; some generic platform advice mixed in that wasn't in BEA's docs
- **1**: Hallucinated advice that contradicts BEA's actual guidance

### Pacing
- **5**: 90-second target hit. No dead air. No rush.
- **3**: Within 10 seconds of target; occasional rush or pause
- **1**: 30+ seconds off target; or unwatchable rush / drag

### Educational effectiveness
- **5**: A new creator could watch this and apply it on their next LIVE
- **3**: Useful as a reminder for someone who already knows the material
- **1**: Doesn't actually teach anything actionable

### Production cost (human-minutes)
- **5**: < 5 minutes per video — fully automated end-to-end
- **3**: 15-30 minutes per video — meaningful manual review needed
- **1**: > 60 minutes per video — automation didn't pay off

### API/compute cost (USD)
- **5**: < $1 per video
- **3**: $1-5 per video
- **1**: > $10 per video — doesn't scale economically

## How to use this

When filling in the decision memo:

1. Score each dimension independently. Don't anchor on the overall feel.
2. If a dimension is hard to score, note why in the table's notes column rather than picking 3 as a default.
3. The recommendation (§6 of the memo) should follow from the scores, not the other way around.
