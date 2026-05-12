"""YouTube Analytics collector.

Pulls per-video engagement stats for BEA training videos. Complements
the in-app playback tracking that already lives in Toklytics-LiveIQ:

- Toklytics tracks: who watched, where in Toklytics, when (in-app context)
- YouTube Analytics tracks: aggregate views, watch time, audience retention
  curve, traffic source — *including* views from forwarded / leaked links
  outside Toklytics

For Phase 1, the most useful single metric is **audience retention curve**:
where do creators drop off in each module? That tells us which slides need
rewriting.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from youtube_auth import get_credentials


@dataclass
class AnalyticsCollector:
    """YouTube Analytics API wrapper for training video reporting."""

    channel_id: str = ""

    def __post_init__(self) -> None:
        # "==" placeholder = "use authenticated user's channel" per API conventions
        self.channel_id = self.channel_id or os.environ.get("YOUTUBE_CHANNEL_ID", "MINE")

    def _client(self) -> Any:
        return build("youtubeAnalytics", "v2", credentials=get_credentials())

    def video_summary(
        self,
        video_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Top-line stats for one video: views, watch time, avg view duration.

        Dates as 'YYYY-MM-DD'. Defaults to last 30 days.
        """
        end_date = end_date or date.today().isoformat()
        start_date = start_date or (date.today() - timedelta(days=30)).isoformat()

        result = (
            self._client()
            .reports()
            .query(
                ids=f"channel=={self.channel_id}" if self.channel_id != "MINE" else "channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
                dimensions="video",
                filters=f"video=={video_id}",
            )
            .execute()
        )
        return _flatten_report(result)

    def retention_curve(
        self,
        video_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, float]]:
        """Per-quantile retention. Tells you where creators drop off.

        Returns a list like:
            [{"elapsedRatio": 0.0, "audienceWatchRatio": 1.0}, ...]
        elapsedRatio is the position in the video (0.0 to 1.0).
        audienceWatchRatio is the fraction of viewers still watching at that point.
        Sharp drops between adjacent rows = slides that lose people.
        """
        end_date = end_date or date.today().isoformat()
        start_date = start_date or (date.today() - timedelta(days=30)).isoformat()

        result = (
            self._client()
            .reports()
            .query(
                ids=f"channel=={self.channel_id}" if self.channel_id != "MINE" else "channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="audienceWatchRatio",
                dimensions="elapsedVideoTimeRatio",
                filters=f"video=={video_id}",
                sort="elapsedVideoTimeRatio",
            )
            .execute()
        )
        rows = result.get("rows", [])
        return [
            {"elapsedRatio": float(r[0]), "audienceWatchRatio": float(r[1])}
            for r in rows
        ]

    def find_drop_off_slides(
        self,
        video_id: str,
        timing_path: Path,
        threshold: float = 0.10,
    ) -> list[dict[str, Any]]:
        """Map retention drops to specific slides.

        Reads the timing.json sidecar (written by video_renderer.py),
        pulls the retention curve, and flags slides where retention drops
        by more than `threshold` (default: 10 percentage points).

        Useful Phase 1+ output for the coaching loop:
            "Module BEA-TRN-0007 loses 23% of viewers at slide 3 —
             that's the slide on compliance disclosures. Consider rewriting."
        """
        timing = json.loads(timing_path.read_text())["slides"]
        if not timing:
            return []
        total_duration = timing[-1]["end_seconds"]

        curve = self.retention_curve(video_id)
        if not curve:
            return []

        drops: list[dict[str, Any]] = []
        for slide in timing:
            slide_start_ratio = slide["start_seconds"] / total_duration
            slide_end_ratio = slide["end_seconds"] / total_duration

            ret_at_start = _interpolate_retention(curve, slide_start_ratio)
            ret_at_end = _interpolate_retention(curve, slide_end_ratio)
            drop = ret_at_start - ret_at_end

            if drop >= threshold:
                drops.append(
                    {
                        "slide_index": slide["index"],
                        "retention_at_start": round(ret_at_start, 3),
                        "retention_at_end": round(ret_at_end, 3),
                        "drop": round(drop, 3),
                    }
                )

        return drops


def _flatten_report(result: dict[str, Any]) -> dict[str, Any]:
    """Convert a Reports API response to {metric_name: value}."""
    headers = result.get("columnHeaders", [])
    rows = result.get("rows", [])
    if not rows:
        return {h["name"]: None for h in headers}
    row = rows[0]
    return {h["name"]: row[i] for i, h in enumerate(headers)}


def _interpolate_retention(curve: list[dict[str, float]], ratio: float) -> float:
    """Linear interpolation of audienceWatchRatio at a given elapsedRatio."""
    if not curve:
        return 1.0
    if ratio <= curve[0]["elapsedRatio"]:
        return curve[0]["audienceWatchRatio"]
    if ratio >= curve[-1]["elapsedRatio"]:
        return curve[-1]["audienceWatchRatio"]

    for i in range(len(curve) - 1):
        lo, hi = curve[i], curve[i + 1]
        if lo["elapsedRatio"] <= ratio <= hi["elapsedRatio"]:
            span = hi["elapsedRatio"] - lo["elapsedRatio"] or 1
            frac = (ratio - lo["elapsedRatio"]) / span
            return lo["audienceWatchRatio"] + frac * (
                hi["audienceWatchRatio"] - lo["audienceWatchRatio"]
            )
    return curve[-1]["audienceWatchRatio"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python analytics_collector.py <video_id> [timing.json]"
        )
        sys.exit(1)

    video_id = sys.argv[1]
    collector = AnalyticsCollector()
    print("Summary:")
    print(json.dumps(collector.video_summary(video_id), indent=2))

    if len(sys.argv) > 2:
        print("\nDrop-off slides:")
        drops = collector.find_drop_off_slides(video_id, Path(sys.argv[2]))
        print(json.dumps(drops, indent=2))
