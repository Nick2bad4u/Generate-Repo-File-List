"""NotebookLM Enterprise REST client.

Uses the official Google Cloud NotebookLM Enterprise API (Preview / v1alpha)
documented at:
    https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks

Auth: OAuth 2.0 bearer token via `gcloud auth print-access-token`. Run
`gcloud auth application-default login` (or `gcloud auth login`) before using.

Prerequisites:
- A Google Cloud project with NotebookLM Enterprise license enabled
- `gcloud` CLI installed and authenticated
- Project number and region (us / eu / global) set in env

Important caveats (Day 1 verifications — DO NOT SKIP):

1. **Audio retrieval:** The audioOverviews POST docs we read describe creation
   and deletion only. Whether the audio file (and transcript) can actually be
   retrieved programmatically is the #1 thing to verify Day 1. If not, the
   spike either:
     - Routes around NotebookLM and uses Claude directly with the source
       corpus (Path A in the runbook), or
     - Treats NotebookLM as voice-only inspiration and uses Claude for the
       slide outline + narration (Path B in the runbook).

2. **Sources endpoint:** The sources management API page returned 404 when we
   looked. Read the official docs to find the actual sources endpoint, or
   create the notebook with sources via the create call if that's supported.

3. **Preview API:** v1alpha can change. Pin to a specific date in your code
   comments if you find behavior that breaks between API versions.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass
class NotebookLMEnterpriseClient:
    """REST client for NotebookLM Enterprise.

    Build with `from_env()`. The orchestrator should never touch raw HTTP.
    """

    project_number: str
    location: str  # one of: us, eu, global
    _token: str | None = None
    _token_expiry: float = 0.0

    @classmethod
    def from_env(cls) -> "NotebookLMEnterpriseClient":
        project = os.environ.get("GCP_PROJECT_NUMBER")
        location = os.environ.get("NOTEBOOKLM_LOCATION", "us")
        if not project:
            raise RuntimeError(
                "GCP_PROJECT_NUMBER not set. See .env.example. Get it from "
                "https://console.cloud.google.com/projectnumber"
            )
        if location not in {"us", "eu", "global"}:
            raise RuntimeError(f"NOTEBOOKLM_LOCATION must be us|eu|global, got {location!r}")
        return cls(project_number=project, location=location)

    # ---- auth ----

    def _access_token(self) -> str:
        """Return a valid bearer token, refreshing via gcloud if expired."""
        now = time.time()
        if self._token and now < self._token_expiry:
            return self._token
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            check=True,
            capture_output=True,
            text=True,
        )
        self._token = result.stdout.strip()
        self._token_expiry = now + 3000  # ~50 min, well under the 60-min lifetime
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token()}",
            "Content-Type": "application/json",
        }

    def _base_url(self) -> str:
        return (
            f"https://{self.location}-discoveryengine.googleapis.com/v1alpha"
            f"/projects/{self.project_number}/locations/{self.location}"
        )

    # ---- notebook lifecycle ----

    def list_recent_notebooks(self) -> list[dict[str, Any]]:
        """notebooks.listRecentlyViewed — Day 1 auth-check method."""
        resp = requests.get(
            f"{self._base_url()}/notebooks:listRecentlyViewed",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("notebooks", [])

    def create_notebook(self, title: str) -> dict[str, Any]:
        """notebooks.create — returns the created notebook resource."""
        resp = requests.post(
            f"{self._base_url()}/notebooks",
            headers=self._headers(),
            json={"title": title},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_notebook(self, notebook_id: str) -> dict[str, Any]:
        """notebooks.get."""
        resp = requests.get(
            f"{self._base_url()}/notebooks/{notebook_id}",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ---- sources (TODO Day 1: verify endpoint shape) ----

    def add_source(self, notebook_id: str, source_path: Path) -> dict[str, Any]:
        """Upload a source document into a notebook.

        TODO Day 1: the sources REST endpoint shape isn't yet documented in the
        page we fetched (it returned 404 on a guess). Find the correct endpoint
        in the Google Cloud docs index for NotebookLM Enterprise and fill in.

        Likely shape based on Discovery Engine conventions:
            POST /notebooks/{notebook_id}/sources
            body: { "displayName": "...", "content": {...} }

        For PDFs, the content may need to be uploaded to a separate Discovery
        Engine document store first, then referenced.
        """
        raise NotImplementedError(
            "TODO Day 1: implement sources upload. See https://docs.cloud.google.com/"
            "gemini/enterprise/notebooklm-enterprise/docs/ for the sources endpoint."
        )

    def list_sources(self, notebook_id: str) -> list[dict[str, Any]]:
        """List sources attached to a notebook.

        TODO Day 1: confirm endpoint shape and fill in.
        """
        raise NotImplementedError("TODO Day 1: implement sources list.")

    # ---- audio overview (the closest thing to a 'generate' call) ----

    def create_audio_overview(
        self,
        notebook_id: str,
        source_ids: list[str],
        episode_focus: str,
        language_code: str = "en-US",
    ) -> dict[str, Any]:
        """audioOverviews.create — kicks off async generation.

        Per the docs: "It takes a few minutes to generate an audio overview."
        Returns immediately with a status; poll get_audio_overview() until
        ready.
        """
        resp = requests.post(
            f"{self._base_url()}/notebooks/{notebook_id}/audioOverviews",
            headers=self._headers(),
            json={
                "sourceIds": [{"id": sid} for sid in source_ids],
                "episodeFocus": episode_focus,
                "languageCode": language_code,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_audio_overview(self, notebook_id: str) -> dict[str, Any]:
        """Get the audio overview status / payload.

        TODO Day 1: verify this endpoint exists and what it returns. The audio
        URL or transcript may or may not be in the response — that's THE
        critical Day 1 question. If neither is retrievable via API, see the
        runbook for the workaround paths.
        """
        resp = requests.get(
            f"{self._base_url()}/notebooks/{notebook_id}/audioOverviews/default",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def wait_for_audio_overview(
        self, notebook_id: str, timeout_seconds: int = 600, poll_seconds: int = 15
    ) -> dict[str, Any]:
        """Poll get_audio_overview until ready or timeout."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            payload = self.get_audio_overview(notebook_id)
            # TODO Day 1: confirm what field signals 'ready'. Likely 'state' or
            # similar. Adjust the comparison to match the actual response.
            state = payload.get("state") or payload.get("status")
            if state in {"READY", "SUCCEEDED", "DONE"}:
                return payload
            if state in {"FAILED", "ERROR"}:
                raise RuntimeError(f"Audio overview failed: {payload}")
            time.sleep(poll_seconds)
        raise TimeoutError(f"Audio overview not ready after {timeout_seconds}s")

    def delete_audio_overview(self, notebook_id: str) -> None:
        """Delete the audio overview (per docs: only one 'default' per notebook)."""
        resp = requests.delete(
            f"{self._base_url()}/notebooks/{notebook_id}/audioOverviews/default",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
