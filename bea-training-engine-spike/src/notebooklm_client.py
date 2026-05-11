"""Thin wrapper around `notebooklm-py` (forked).

This module is intentionally a skeleton — the precise API surface depends on
the fork's actual implementation, which you read at the start of Day 1 of the
runbook. Fill in the TODOs after reading `forks/notebooklm-py/README.md`.

Design intent:
- Keep all `notebooklm-py` import / call surface area in this one file
- The orchestrator imports `NotebookLMClient` and never touches the underlying
  fork directly
- When Phase 1 replaces this with a real service, only this file changes
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# TODO Day 1: replace with the actual import the fork exposes.
# Example: `from notebooklm import Client as NLMClient`
# Read forks/notebooklm-py/README.md to find the right import path.
# If the fork isn't a proper package, you may need:
#     sys.path.insert(0, "forks/notebooklm-py")
#     import notebooklm
# Document whichever path works once you find it.


@dataclass
class NotebookLMClient:
    """Wrapper that hides the upstream API behind methods the orchestrator calls."""

    # Whatever auth artifact the fork needs. Could be a cookie string, an OAuth
    # token, a path to a cookies.txt file, etc. Pick what matches the README.
    auth_token: str

    @classmethod
    def from_env(cls) -> "NotebookLMClient":
        """Build a client from environment variables.

        TODO Day 1: pick the right env var per the fork's auth method. Common:
            - NOTEBOOKLM_COOKIE (session cookie string)
            - GOOGLE_OAUTH_REFRESH_TOKEN (OAuth flow)
            - NOTEBOOKLM_COOKIES_FILE (path to cookies.txt)
        Update .env.example to match.
        """
        token = (
            os.environ.get("NOTEBOOKLM_COOKIE")
            or os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")
            or os.environ.get("NOTEBOOKLM_COOKIES_FILE")
        )
        if not token:
            raise RuntimeError(
                "No NotebookLM auth found in env. See .env.example and "
                "forks/notebooklm-py/README.md for which env var the fork uses."
            )
        return cls(auth_token=token)

    # ---- core methods the orchestrator calls ----

    def list_notebooks(self) -> list[str]:
        """Return a list of notebook IDs or names visible to the authenticated user.

        Day 1 success criterion: this method returns non-empty (or empty but no
        error) — proves the auth path works end-to-end.

        TODO: implement using the fork's list-notebooks call.
        """
        raise NotImplementedError("TODO Day 1: implement via notebooklm-py")

    def create_or_get_notebook(self, name: str) -> str:
        """Create a notebook with the given name, or return an existing one.

        Returns the notebook ID (whatever string identifier the fork uses).

        TODO: implement.
        """
        raise NotImplementedError("TODO Day 1: implement via notebooklm-py")

    def upload_source(self, notebook_id: str, doc_path: Path) -> None:
        """Upload a single source document to the notebook.

        TODO: implement. Fork may expose this as `upload_pdf`, `add_source`,
        `upload_file`, or similar — check the README.
        """
        raise NotImplementedError("TODO Day 1: implement via notebooklm-py")

    def generate_overview(self, notebook_id: str) -> dict[str, Any]:
        """Day 1 EOD: produce *some* generated output about the uploaded sources.

        Could be: audio overview, study guide, briefing doc, FAQ, etc. Pick the
        one with the cleanest API. The point is to prove generation works.

        Returns a dict (whatever structure the fork returns).

        TODO: implement.
        """
        raise NotImplementedError("TODO Day 1: implement via notebooklm-py")

    def generate_deck(
        self,
        notebook_id: str,
        topic: str,
        slide_count: int,
        target_seconds: int,
        slide_outline_prompt: str,
        narration_prompt: str,
    ) -> dict[str, Any]:
        """Day 2: produce a slide deck + narration script for the topic.

        Likely a two-step process:
        1. Call NotebookLM with the slide-outline prompt + topic → get an
           outline grounded in the uploaded sources.
        2. For each slide, expand to narration text using the narration prompt.

        Return shape (suggested — adapt to fit the renderer):
            {
              "topic": "...",
              "target_seconds": 90,
              "slides": [
                {"index": 1, "title": "...", "bullets": [...], "narration": "..."},
                ...
              ],
              "sources_cited": [...]
            }

        TODO: implement.
        """
        raise NotImplementedError("TODO Day 2: implement via notebooklm-py")
