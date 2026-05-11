"""BEA Training Engine — Phase 0 Spike Orchestrator.

CLI walks through the 3-day spike, retargeted to use the official
NotebookLM Enterprise REST API (gcloud auth) instead of the unofficial fork.

Day 1:
    python src/spike_orchestrator.py auth
    python src/spike_orchestrator.py create-notebook
    python src/spike_orchestrator.py upload-sources --inputs inputs/
    python src/spike_orchestrator.py kick-audio-overview

Day 2:
    python src/spike_orchestrator.py fetch-audio-overview
    python src/spike_orchestrator.py derive-deck
    python src/spike_orchestrator.py render-video

Day 3:
    Open evaluation/decision-memo.md and fill it in.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console

from notebooklm_client import NotebookLMEnterpriseClient
from slide_deriver import ClaudeSlideDeriver
from video_renderer import VideoRenderer

load_dotenv()
console = Console()

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", ROOT / "outputs"))
PROMPTS_DIR = ROOT / "prompts"
BRAND_THEME = Path(os.environ.get("BRAND_THEME_PATH", ROOT / "brand/theme.json"))


@click.group()
def cli() -> None:
    """Phase 0 spike orchestrator (Enterprise API path)."""


# ----- Day 1 -----


@cli.command()
def auth() -> None:
    """Day 1: verify gcloud + NotebookLM Enterprise API + Anthropic key all work."""
    console.rule("[bold blue]Day 1 — auth check")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY missing in .env[/red]")
        sys.exit(1)
    console.print("[green]Anthropic key present[/green]")

    client = NotebookLMEnterpriseClient.from_env()
    notebooks = client.list_recent_notebooks()
    console.print(
        f"[green]NotebookLM Enterprise auth OK[/green] — "
        f"found {len(notebooks)} recent notebook(s)"
    )
    for nb in notebooks[:5]:
        console.print(f"  - {nb.get('title', '<untitled>')} ({nb.get('name', '?')})")


@cli.command("create-notebook")
@click.option(
    "--title",
    default="BEA Training Spike",
    help="NotebookLM notebook title.",
)
def create_notebook(title: str) -> None:
    """Day 1: create a notebook in NotebookLM Enterprise."""
    console.rule(f"[bold blue]Day 1 — creating notebook: {title}")
    client = NotebookLMEnterpriseClient.from_env()
    nb = client.create_notebook(title)
    notebook_id = _extract_notebook_id(nb)
    console.print(f"[green]Created notebook {notebook_id}[/green]")
    _stash({"notebook_id": notebook_id, "title": title}, "state.json")


@cli.command("upload-sources")
@click.option(
    "--inputs",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=ROOT / "inputs",
    help="Directory containing BEA source docs (markdown/pdf/txt).",
)
def upload_sources(inputs: Path) -> None:
    """Day 1: upload BEA source docs to the notebook.

    NOTE: the sources REST endpoint shape isn't fully documented yet (the docs
    page returned 404 on a guess). Verify the endpoint and adapt
    notebooklm_client.add_source() before running this command.
    """
    console.rule(f"[bold blue]Day 1 — uploading sources from {inputs}")
    state = _load("state.json")
    notebook_id = state["notebook_id"]

    docs = sorted(p for p in inputs.iterdir() if p.suffix.lower() in {".md", ".pdf", ".txt"})
    if not docs:
        console.print(f"[red]No source docs found in {inputs}[/red]")
        sys.exit(1)

    client = NotebookLMEnterpriseClient.from_env()
    source_ids: list[str] = []
    for doc in docs:
        console.print(f"  Uploading {doc.name}")
        result = client.add_source(notebook_id, doc)
        sid = result.get("id") or result.get("name", "").split("/")[-1]
        if sid:
            source_ids.append(sid)

    console.print(f"[green]Uploaded {len(source_ids)} source(s)[/green]")
    state["source_ids"] = source_ids
    _stash(state, "state.json")


@cli.command("kick-audio-overview")
@click.option(
    "--topic",
    default=os.environ.get("SPIKE_TOPIC", "How to acknowledge a gifter on TikTok LIVE"),
    help="Episode focus for the audio overview.",
)
def kick_audio_overview(topic: str) -> None:
    """Day 1: kick off async audio overview generation. Takes a few minutes."""
    console.rule(f"[bold blue]Day 1 — kicking audio overview: {topic}")
    state = _load("state.json")
    client = NotebookLMEnterpriseClient.from_env()
    result = client.create_audio_overview(
        notebook_id=state["notebook_id"],
        source_ids=state.get("source_ids", []),
        episode_focus=topic,
    )
    console.print(f"[green]Audio overview kicked. Initial state: {result.get('state', '?')}[/green]")
    console.print("Wait a few minutes, then run: fetch-audio-overview")


# ----- Day 2 -----


@cli.command("fetch-audio-overview")
def fetch_audio_overview() -> None:
    """Day 2 morning: poll until audio overview is ready, then save it.

    THE CRITICAL DAY 1 VERIFICATION: does the response include the audio file
    URL and/or transcript? If not, we have to route around NotebookLM for the
    actual content. See the runbook for fallback paths.
    """
    console.rule("[bold blue]Day 2 — fetching audio overview")
    state = _load("state.json")
    client = NotebookLMEnterpriseClient.from_env()
    payload = client.wait_for_audio_overview(state["notebook_id"])

    # Save raw payload so we can inspect what fields are actually returned
    out = OUTPUT_DIR / "01-audio-overview.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    console.print(f"[green]Saved raw payload to {out}[/green]")
    console.print(
        "[yellow]NOW INSPECT IT.[/yellow] Does it contain an audio URL? "
        "A transcript? If neither, see runbook §Day-1-blocker-paths."
    )


@cli.command("derive-deck")
@click.option(
    "--topic",
    default=os.environ.get("SPIKE_TOPIC", "How to acknowledge a gifter on TikTok LIVE"),
    help="Topic for the training video.",
)
@click.option("--slides", default=6, type=int)
@click.option("--seconds", default=90, type=int)
@click.option(
    "--inputs",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=ROOT / "inputs",
    help="Source docs directory (used as additional context for Claude).",
)
def derive_deck(topic: str, slides: int, seconds: int, inputs: Path) -> None:
    """Day 2: derive a slide deck + narration via Claude.

    Uses the audio overview transcript (if available) plus the source corpus
    as Claude's grounding. Outputs a deck.json that the renderer consumes.
    """
    console.rule(f"[bold blue]Day 2 — deriving deck for: {topic}")

    transcript_path = OUTPUT_DIR / "01-audio-overview.json"
    transcript = ""
    if transcript_path.exists():
        payload = json.loads(transcript_path.read_text())
        transcript = (
            payload.get("transcript")
            or payload.get("transcriptText")
            or _walk_for_transcript(payload)
            or ""
        )
        if transcript:
            console.print(f"[green]Using transcript ({len(transcript)} chars) as Claude context[/green]")
        else:
            console.print(
                "[yellow]Audio overview payload has no transcript field. "
                "Falling back to source corpus only.[/yellow]"
            )

    source_texts = _load_sources(inputs)

    deriver = ClaudeSlideDeriver()
    deck = deriver.derive(
        topic=topic,
        slide_count=slides,
        target_seconds=seconds,
        transcript=transcript,
        source_texts=source_texts,
        slide_outline_prompt=(PROMPTS_DIR / "slide-outline.md").read_text(),
        narration_prompt=(PROMPTS_DIR / "narration.md").read_text(),
    )

    deck_dir = OUTPUT_DIR / "01-deck-spike"
    deck_dir.mkdir(parents=True, exist_ok=True)
    (deck_dir / "deck.json").write_text(json.dumps(deck, indent=2))
    console.print(f"[green]Deck saved to {deck_dir / 'deck.json'}[/green]")
    console.print("Read the script aloud before continuing — sanity check.")


@cli.command("render-video")
@click.option(
    "--deck",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
def render_video(deck: Path) -> None:
    """Day 2 afternoon: render the deck to MP4."""
    console.rule(f"[bold blue]Day 2 — rendering video from {deck}")

    deck_data = json.loads(deck.read_text())
    brand = json.loads(BRAND_THEME.read_text())

    renderer = VideoRenderer(brand=brand)
    output_path = OUTPUT_DIR / "01-video-spike.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    renderer.render(deck_data, output_path)
    console.print(f"[green]Video rendered to {output_path}[/green]")


# ----- helpers -----


def _extract_notebook_id(nb: dict) -> str:
    # Notebook resource name is like:
    # "projects/PROJECT/locations/LOCATION/notebooks/NOTEBOOK_ID"
    name = nb.get("name", "")
    return name.split("/")[-1] if name else nb.get("id", "")


def _walk_for_transcript(obj, depth: int = 0):
    """Heuristic: walk a nested response looking for a long text-like field."""
    if depth > 5:
        return None
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and len(v) > 500 and any(
                t in k.lower() for t in ("transcript", "text", "content", "script")
            ):
                return v
            found = _walk_for_transcript(v, depth + 1)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _walk_for_transcript(item, depth + 1)
            if found:
                return found
    return None


def _load_sources(inputs: Path) -> list[dict]:
    """Read source docs as plain text for Claude context."""
    out = []
    for p in sorted(inputs.iterdir()):
        if p.suffix.lower() in {".md", ".txt"}:
            out.append({"name": p.name, "text": p.read_text()})
        elif p.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader

                text = "\n".join(page.extract_text() or "" for page in PdfReader(p).pages)
                out.append({"name": p.name, "text": text})
            except Exception as e:
                console.print(f"[yellow]Skipping {p.name}: {e}[/yellow]")
    return out


def _stash(data: dict, name: str) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _load(name: str) -> dict:
    path = OUTPUT_DIR / name
    if not path.exists():
        console.print(f"[red]Expected state file {path} not found. Did you run earlier steps?[/red]")
        sys.exit(1)
    return json.loads(path.read_text())


if __name__ == "__main__":
    cli()
