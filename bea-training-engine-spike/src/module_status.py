"""Module review state machine + local persistence.

Implements the workflow defined in docs/bea-training-engine-editorial-workflow.md
as a local CLI scaffold. State persists in outputs/review-state.json. Production
Phase 1 replaces this with calls to Toklytics-LiveIQ's tRPC endpoint, but the
state machine itself stays identical.

Why local for the spike:
- Lets us validate the contract before LiveIQ team builds the dashboard
- Lets a single developer exercise the full pipeline solo
- Gives us a concrete reference implementation when LiveIQ wires up the server side
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class Status(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


# Allowed transitions per state machine in the design doc.
TRANSITIONS: dict[Status, set[Status]] = {
    Status.DRAFT: {Status.PENDING_REVIEW, Status.ARCHIVED},
    Status.PENDING_REVIEW: {Status.APPROVED, Status.REJECTED, Status.DRAFT},
    Status.APPROVED: {Status.PUBLISHED, Status.ARCHIVED},
    Status.REJECTED: {Status.ARCHIVED, Status.DRAFT},  # DRAFT for regenerate-after-rejection
    Status.PUBLISHED: {Status.DEPRECATED},
    Status.DEPRECATED: {Status.ARCHIVED},
    Status.ARCHIVED: set(),
}


# Keyword heuristic for the compliance flag. See design doc §"Compliance flagging".
COMPLIANCE_KEYWORDS = [
    "payout", "earnings", "income", "tax", "refund", "chargeback",
    "violation", "ban", "strike", "appeal", "shadow", "shadowban",
    "sponsor", " ad ", "promotion", "endorsement", "ftc", "disclose",
    "minor", "child", "underage", "safety",
]


REJECT_REASONS = {
    "factual",
    "mispronunciation",
    "off-brand",
    "off-topic",
    "compliance",
    "cost",
    "other",
}


@dataclass
class ModuleRecord:
    module_id: str
    language: str
    status: str = Status.DRAFT.value
    artifact_url: str | None = None
    deck_url: str | None = None
    timing_url: str | None = None
    captions_url: str | None = None
    thumbnail_url: str | None = None
    source_commit_sha: str | None = None
    prompt_template_ver: str | None = None
    ai_cost_usd: float | None = None
    submitted_at: str | None = None
    submitted_by: str | None = None
    decided_at: str | None = None
    decided_by: str | None = None
    decision_reason: str | None = None
    decision_slide_index: int | None = None
    decision_notes: str | None = None
    compliance_flagged: bool = False
    youtube_video_id: str | None = None
    audit: list[dict[str, Any]] = field(default_factory=list)


class StatusError(Exception):
    """Raised on invalid state transition or invalid input."""


def _state_path() -> Path:
    return Path(os.environ.get("OUTPUT_DIR", "./outputs")) / "review-state.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state() -> dict[str, ModuleRecord]:
    path = _state_path()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return {k: ModuleRecord(**v) for k, v in raw.items()}


def _save_state(state: dict[str, ModuleRecord]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = {k: asdict(v) for k, v in state.items()}
    path.write_text(json.dumps(serializable, indent=2))


def _audit(record: ModuleRecord, actor: str, action: str, from_status: str, to_status: str, notes: str | None) -> None:
    record.audit.append(
        {
            "actor": actor,
            "action": action,
            "from_status": from_status,
            "to_status": to_status,
            "notes": notes,
            "occurred_at": _now(),
        }
    )


def _transition(record: ModuleRecord, to: Status, actor: str, action: str, notes: str | None = None) -> None:
    current = Status(record.status)
    if to not in TRANSITIONS[current]:
        raise StatusError(
            f"Illegal transition for {record.module_id}: {current.value} → {to.value}. "
            f"Allowed: {sorted(s.value for s in TRANSITIONS[current])}"
        )
    _audit(record, actor, action, current.value, to.value, notes)
    record.status = to.value


def detect_compliance(deck: dict[str, Any]) -> bool:
    """Return True if any compliance keyword appears in the deck's narration."""
    combined = " ".join(
        (slide.get("narration") or "").lower() for slide in deck.get("slides", [])
    )
    return any(k in combined for k in COMPLIANCE_KEYWORDS)


# ---- public API used by the orchestrator ----


def submit(
    module_id: str,
    language: str,
    deck: dict[str, Any],
    artifact_url: str | None = None,
    deck_url: str | None = None,
    timing_url: str | None = None,
    captions_url: str | None = None,
    thumbnail_url: str | None = None,
    source_commit_sha: str | None = None,
    prompt_template_ver: str | None = None,
    ai_cost_usd: float | None = None,
    actor: str = "engine",
) -> ModuleRecord:
    """Submit a new module for review. Creates if absent; moves to PENDING_REVIEW."""
    state = _load_state()
    record = state.get(_key(module_id, language)) or ModuleRecord(
        module_id=module_id, language=language
    )
    record.artifact_url = artifact_url
    record.deck_url = deck_url
    record.timing_url = timing_url
    record.captions_url = captions_url
    record.thumbnail_url = thumbnail_url
    record.source_commit_sha = source_commit_sha
    record.prompt_template_ver = prompt_template_ver
    record.ai_cost_usd = ai_cost_usd
    record.submitted_at = _now()
    record.submitted_by = actor
    record.compliance_flagged = detect_compliance(deck)

    if Status(record.status) == Status.DRAFT:
        _transition(record, Status.PENDING_REVIEW, actor, "submit", None)
    else:
        # Already in review or further along — refresh artifacts but don't move state
        _audit(record, actor, "resubmit", record.status, record.status, "artifacts refreshed")

    state[_key(module_id, language)] = record
    _save_state(state)
    return record


def approve(module_id: str, language: str, actor: str, notes: str | None = None) -> ModuleRecord:
    state = _load_state()
    record = state[_key(module_id, language)]
    if record.compliance_flagged and actor.split(":")[0] != "senior_editor":
        raise StatusError(
            f"Module {module_id} is compliance-flagged; needs a senior_editor. "
            f"Got: {actor}"
        )
    _transition(record, Status.APPROVED, actor, "approve", notes)
    record.decided_at = _now()
    record.decided_by = actor
    record.decision_notes = notes
    _save_state(state)
    return record


def reject(
    module_id: str,
    language: str,
    actor: str,
    reason: str,
    slide_index: int | None = None,
    notes: str | None = None,
) -> ModuleRecord:
    if reason not in REJECT_REASONS:
        raise StatusError(f"Invalid reason: {reason}. Allowed: {sorted(REJECT_REASONS)}")
    state = _load_state()
    record = state[_key(module_id, language)]
    _transition(record, Status.REJECTED, actor, "reject", f"{reason}: {notes or ''}".strip())
    record.decided_at = _now()
    record.decided_by = actor
    record.decision_reason = reason
    record.decision_slide_index = slide_index
    record.decision_notes = notes
    _save_state(state)
    return record


def request_changes(
    module_id: str,
    language: str,
    actor: str,
    reason: str,
    slide_index: int | None = None,
    notes: str | None = None,
) -> ModuleRecord:
    """Like reject, but moves back to DRAFT for regeneration with the rejection hint."""
    if reason not in REJECT_REASONS:
        raise StatusError(f"Invalid reason: {reason}")
    state = _load_state()
    record = state[_key(module_id, language)]
    _transition(record, Status.DRAFT, actor, "request_changes", f"{reason}: {notes or ''}".strip())
    record.decision_reason = reason
    record.decision_slide_index = slide_index
    record.decision_notes = notes
    _save_state(state)

    # Write a sibling rejection.json the next derive-deck pass picks up
    _write_rejection_hint(module_id, language, reason, slide_index, notes)
    return record


def mark_published(module_id: str, language: str, youtube_video_id: str, actor: str = "engine") -> ModuleRecord:
    state = _load_state()
    record = state[_key(module_id, language)]
    _transition(record, Status.PUBLISHED, actor, "publish", f"youtube_video_id={youtube_video_id}")
    record.youtube_video_id = youtube_video_id
    _save_state(state)
    return record


def require_approved(module_id: str, language: str) -> ModuleRecord:
    """Used by youtube_publisher as a publish-time gate."""
    state = _load_state()
    record = state.get(_key(module_id, language))
    if record is None:
        raise StatusError(f"Module {module_id} ({language}) has no review record")
    if Status(record.status) != Status.APPROVED:
        raise StatusError(
            f"Module {module_id} ({language}) is {record.status}, not APPROVED. "
            f"Cannot publish."
        )
    return record


def list_pending() -> list[ModuleRecord]:
    return [
        r for r in _load_state().values()
        if Status(r.status) == Status.PENDING_REVIEW
    ]


def get(module_id: str, language: str) -> ModuleRecord | None:
    return _load_state().get(_key(module_id, language))


def _key(module_id: str, language: str) -> str:
    return f"{module_id}:{language}"


def _write_rejection_hint(
    module_id: str,
    language: str,
    reason: str,
    slide_index: int | None,
    notes: str | None,
) -> None:
    """Drop a rejection.json next to the deck so the next derive picks it up."""
    deck_dir = Path(os.environ.get("OUTPUT_DIR", "./outputs")) / "01-deck-spike"
    deck_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if language == "en-US" else f"-{language}"
    hint_path = deck_dir / f"rejection{suffix}.json"
    hint_path.write_text(
        json.dumps(
            {
                "module_id": module_id,
                "language": language,
                "reason": reason,
                "slide_index": slide_index,
                "notes": notes,
                "written_at": _now(),
            },
            indent=2,
        )
    )
