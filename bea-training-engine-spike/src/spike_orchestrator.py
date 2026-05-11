"""BEA Training Engine — Phase 0 Spike Orchestrator.

CLI that walks through the 3-day spike per the runbook. Each command maps to a
runbook step; bodies contain TODOs where API specifics need to be filled in
after reading the forks' READMEs.

Usage:
    python src/spike_orchestrator.py auth
    python src/spike_orchestrator.py upload --inputs inputs/
    python src/spike_orchestrator.py test-generate
    python src/spike_orchestrator.py generate-deck --topic "..."
    python src/spike_orchestrator.py render-video --deck outputs/01-deck-spike/deck.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console

from notebooklm_client import NotebookLMClient
from video_renderer import VideoRenderer

load_dotenv()
console = Console()

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", ROOT / "outputs"))
PROMPTS_DIR = ROOT / "prompts"
BRAND_THEME = Path(os.environ.get("BRAND_THEME_PATH", ROOT / "brand/theme.json"))


@click.group()
def cli() -> None:
    """Phase 0 spike orchestrator."""


# ----- Day 1 -----


@cli.command()
def auth() -> None:
    """Day 1 / afternoon: verify NotebookLM auth works programmatically."""
    console.rule("[bold blue]Day 1 — NotebookLM auth check")
    client = NotebookLMClient.from_env()
    notebooks = client.list_notebooks()
    console.print(f"[green]Auth OK[/green] — found {len(notebooks)} notebook(s)")
    for nb in notebooks[:5]:
        console.print(f"  - {nb}")


@cli.command()
@click.option(
    "--inputs",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=ROOT / "inputs",
    help="Directory containing BEA source docs (markdown/pdf).",
)
@click.option(
    "--notebook-name",
    default="BEA Training Spike",
    help="NotebookLM notebook to create or reuse.",
)
def upload(inputs: Path, notebook_name: str) -> None:
    """Day 1: upload BEA source docs to a NotebookLM notebook."""
    console.rule(f"[bold blue]Day 1 — uploading sources from {inputs}")
    client = NotebookLMClient.from_env()
    notebook_id = client.create_or_get_notebook(notebook_name)

    docs = sorted(p for p in inputs.iterdir() if p.suffix.lower() in {".md", ".pdf", ".txt"})
    if not docs:
        console.print(f"[red]No source docs found in {inputs}[/red]")
        sys.exit(1)

    for doc in docs:
        console.print(f"  Uploading {doc.name}")
        client.upload_source(notebook_id, doc)

    console.print(f"[green]Uploaded {len(docs)} doc(s) to notebook {notebook_id}[/green]")
    _stash({"notebook_id": notebook_id, "doc_count": len(docs)}, "state.json")


@cli.command("test-generate")
def test_generate() -> None:
    """Day 1 EOD: prove we can get *some* output from NotebookLM about the sources."""
    console.rule("[bold blue]Day 1 — test generation")
    state = _load("state.json")
    notebook_id = state["notebook_id"]

    client = NotebookLMClient.from_env()
    # Pick whichever generation type notebooklm-py exposes most cleanly:
    # audio overview, study guide, briefing doc, etc.
    result = client.generate_overview(notebook_id)
    out = OUTPUT_DIR / "01-day1-overview.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    console.print(f"[green]Saved overview to {out}[/green]")


# ----- Day 2 -----


@cli.command("generate-deck")
@click.option(
    "--topic",
    default=os.environ.get("SPIKE_TOPIC", "How to acknowledge a gifter on TikTok LIVE"),
    help="Topic for the training video.",
)
@click.option("--slides", default=6, type=int)
@click.option("--seconds", default=90, type=int)
def generate_deck(topic: str, slides: int, seconds: int) -> None:
    """Day 2 morning: produce a slide deck + narration from the notebook + topic."""
    console.rule(f"[bold blue]Day 2 — generating deck for: {topic}")
    state = _load("state.json")
    notebook_id = state["notebook_id"]

    client = NotebookLMClient.from_env()

    slide_outline_prompt = (PROMPTS_DIR / "slide-outline.md").read_text()
    narration_prompt = (PROMPTS_DIR / "narration.md").read_text()

    deck = client.generate_deck(
        notebook_id=notebook_id,
        topic=topic,
        slide_count=slides,
        target_seconds=seconds,
        slide_outline_prompt=slide_outline_prompt,
        narration_prompt=narration_prompt,
    )

    deck_dir = OUTPUT_DIR / "01-deck-spike"
    deck_dir.mkdir(parents=True, exist_ok=True)
    (deck_dir / "deck.json").write_text(json.dumps(deck, indent=2))
    console.print(f"[green]Deck saved to {deck_dir / 'deck.json'}[/green]")
    console.print("Review the script aloud before continuing — sanity check.")


@cli.command("render-video")
@click.option(
    "--deck",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
def render_video(deck: Path) -> None:
    """Day 2 afternoon: render the deck to MP4 via training-video-generator."""
    console.rule(f"[bold blue]Day 2 — rendering video from {deck}")

    deck_data = json.loads(deck.read_text())
    brand = json.loads(BRAND_THEME.read_text())

    renderer = VideoRenderer(brand=brand)
    output_path = OUTPUT_DIR / "01-video-spike.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    renderer.render(deck_data, output_path)
    console.print(f"[green]Video rendered to {output_path}[/green]")
    console.print("Open it. Watch it twice. Move to Day 3 (evaluation).")


# ----- helpers -----


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
