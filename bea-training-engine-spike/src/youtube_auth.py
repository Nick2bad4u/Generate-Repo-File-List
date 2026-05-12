"""YouTube OAuth setup + credential loader.

Two entry points:

1. `python src/youtube_auth.py` (CLI) — runs the one-time OAuth consent flow
   for the @boldevolution channel. A channel admin runs this once, consents
   in the browser, and the refresh token is saved to disk.

2. `from youtube_auth import get_credentials` (library) — used by
   youtube_publisher.py and analytics_collector.py to load the saved token
   on each run. Refreshes automatically when the access token expires.

Scopes:
- youtube.upload: required for videos.insert, thumbnails.set, captions.insert
- yt-analytics.readonly: required for the Analytics API

Both scopes are requested up front so the admin only consents once.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _client_secret_path() -> Path:
    return Path(
        os.environ.get("YOUTUBE_CLIENT_SECRET", "./secrets/youtube-client-secret.json")
    )


def _token_path() -> Path:
    return Path(os.environ.get("YOUTUBE_TOKEN_FILE", "./secrets/youtube-token.json"))


def get_credentials() -> Credentials:
    """Load saved credentials, refreshing the access token if needed.

    Raises if the token file doesn't exist — run `python youtube_auth.py`
    first to create it.
    """
    token_path = _token_path()
    if not token_path.exists():
        raise RuntimeError(
            f"No YouTube token at {token_path}. Run `python src/youtube_auth.py` "
            "as a @boldevolution channel admin to set it up."
        )

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
        else:
            raise RuntimeError(
                "YouTube token is invalid and has no refresh token. "
                "Re-run `python src/youtube_auth.py`."
            )
    return creds


def setup_flow() -> None:
    """One-time OAuth consent. Opens a browser, saves the refresh token."""
    secret = _client_secret_path()
    if not secret.exists():
        raise RuntimeError(
            f"Client secret file not found at {secret}. "
            "Download it from Google Cloud Console > APIs & Services > "
            "Credentials > OAuth 2.0 Client IDs (Desktop application)."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    # Use a local server on a random port; flow opens browser to consent URL.
    creds = flow.run_local_server(port=0, prompt="consent")

    token_path = _token_path()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())

    print(f"\n✅ YouTube credentials saved to {token_path}")
    print("This token can refresh itself; you won't be prompted again unless it's revoked.")
    print(
        "\nSanity check: token now has scopes "
        f"{json.loads(token_path.read_text()).get('scopes', '?')}"
    )


if __name__ == "__main__":
    setup_flow()
