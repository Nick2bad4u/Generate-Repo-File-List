"""YouTube Data API v3 publisher for BEA training videos.

Uploads MP4 + thumbnail + SRT captions to @boldevolution, defaulting to
unlisted with AI-content disclosure in the description.

Inputs:
- video_path: the rendered MP4
- module: a dict describing the training module (title, description, tags,
  topic, etc.)
- thumbnail_path: optional PNG/JPG, < 2MB, 1280x720 ideal
- captions_path: optional SRT file

Outputs:
- video_id (YouTube ID)
- video_url (https://youtu.be/...)
- caption_id (if uploaded)

Quota notes: videos.insert costs ~1,600 units. Default 10,000/day = ~6
uploads. If batch-publishing a back catalog, request a quota increase.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from youtube_auth import get_credentials


AI_DISCLOSURE_BOILERPLATE = (
    "\n\n---\n"
    "Narration in this video is AI-generated. Content is sourced from "
    "Bold Evolution Agency creator coaching materials. Internal training "
    "for BEA's TikTok LIVE creator network."
)


@dataclass
class YouTubePublisher:
    privacy_status: str = ""
    category_id: str = ""
    language: str = "en"

    def __post_init__(self) -> None:
        self.privacy_status = self.privacy_status or os.environ.get(
            "YOUTUBE_DEFAULT_PRIVACY", "unlisted"
        )
        self.category_id = self.category_id or os.environ.get(
            "YOUTUBE_DEFAULT_CATEGORY", "27"  # Education
        )
        if self.privacy_status not in {"unlisted", "private", "public"}:
            raise ValueError(f"Invalid privacy_status: {self.privacy_status}")

    def _client(self) -> Any:
        return build("youtube", "v3", credentials=get_credentials())

    def publish(
        self,
        video_path: Path,
        module: dict[str, Any],
        thumbnail_path: Path | None = None,
        captions_path: Path | None = None,
        playlist_id: str | None = None,
        post_upload_thumbnail_fn=None,
    ) -> dict[str, Any]:
        """Upload video + optional thumbnail + optional captions + optional playlist.

        Two thumbnail patterns:
        - `thumbnail_path` (pre-upload): static file applied during this call.
          Use this for PIL-rendered or pre-generated thumbnails.
        - `post_upload_thumbnail_fn` (post-upload): callable taking the
          uploaded video's YouTube URL, returning a Path to the generated
          thumbnail PNG. Used by the YouTube-Thumbnail tool's video_url mode,
          which needs the video on YouTube before it can analyze content.

        The playlist is BEA's handoff to Toklytics-LiveIQ: Toklytics presents
        the training catalog by reading the @boldevolution training playlists.
        Adding the video to the right playlist is what makes it appear in the
        creator app — there's no DB write or separate manifest needed.
        """
        if not video_path.exists():
            raise FileNotFoundError(video_path)

        youtube = self._client()

        # ---- 1. Upload video ----
        title = module.get("title", "BEA Training")[:100]  # YouTube limit
        description = (
            module.get("description", "")
            + AI_DISCLOSURE_BOILERPLATE
        )[:5000]  # YouTube limit
        tags = (module.get("topic_tags") or [])[:30]

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": self.category_id,
                "defaultLanguage": self.language,
                "defaultAudioLanguage": self.language,
            },
            "status": {
                "privacyStatus": self.privacy_status,
                "selfDeclaredMadeForKids": False,
                # YouTube's altered-content flag for AI-generated narration.
                # Field name as of 2026; check current API if rejected.
                "containsSyntheticMedia": True,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            chunksize=-1,  # single shot; switch to chunked for very large files
            resumable=True,
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"  Upload progress: {pct}%")

        video_id = response["id"]
        result: dict[str, Any] = {
            "video_id": video_id,
            "video_url": f"https://youtu.be/{video_id}",
            "privacy_status": self.privacy_status,
        }

        # ---- 2. Thumbnail (pre-upload, static file) ----
        if thumbnail_path and thumbnail_path.exists():
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path)),
            ).execute()
            result["thumbnail_set"] = True
        elif post_upload_thumbnail_fn is not None:
            # ---- 2b. Thumbnail (post-upload, from video URL) ----
            # Let the callback generate a thumbnail using the live YouTube URL.
            # This is the path for YouTube-Thumbnail's video_url mode where
            # the tool downloads + analyzes the video before generating.
            generated_path = post_upload_thumbnail_fn(result["video_url"])
            if generated_path and Path(generated_path).exists():
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(generated_path)),
                ).execute()
                result["thumbnail_set"] = True
                result["thumbnail_source"] = "post_upload_callback"

        # ---- 3. Captions ----
        if captions_path and captions_path.exists():
            cap_response = (
                youtube.captions()
                .insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "language": self.language,
                            "name": "English",
                            "isDraft": False,
                        }
                    },
                    media_body=MediaFileUpload(
                        str(captions_path), mimetype="application/octet-stream"
                    ),
                )
                .execute()
            )
            result["caption_id"] = cap_response["id"]

        # ---- 4. Playlist (the Toklytics handoff) ----
        if playlist_id:
            playlist_item = (
                youtube.playlistItems()
                .insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id,
                            },
                        }
                    },
                )
                .execute()
            )
            result["playlist_id"] = playlist_id
            result["playlist_item_id"] = playlist_item["id"]
            result["toklytics_handoff"] = True

        return result

    def list_playlists(self) -> list[dict[str, Any]]:
        """Return playlists owned by the authenticated channel.

        Useful for picking the right playlist ID during setup, or for
        confirming the configured ID still exists.
        """
        youtube = self._client()
        playlists: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            response = (
                youtube.playlists()
                .list(part="snippet", mine=True, maxResults=50, pageToken=page_token)
                .execute()
            )
            for item in response.get("items", []):
                playlists.append(
                    {
                        "id": item["id"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"].get("description", ""),
                    }
                )
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return playlists

    def remove_from_playlist(self, playlist_item_id: str) -> None:
        """Remove a video from a playlist (used during module deprecation).

        Note: `playlist_item_id` is NOT the video ID — it's the membership
        record returned by publish(). Save it when publishing so deprecation
        can find the right row to delete.
        """
        self._client().playlistItems().delete(id=playlist_item_id).execute()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print(
            "Usage: python youtube_publisher.py <video.mp4> <module.json> "
            "[thumbnail.png] [captions.srt]"
        )
        sys.exit(1)

    module = json.loads(Path(sys.argv[2]).read_text())
    thumb = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    caps = Path(sys.argv[4]) if len(sys.argv) > 4 else None

    publisher = YouTubePublisher()
    result = publisher.publish(Path(sys.argv[1]), module, thumb, caps)
    print(json.dumps(result, indent=2))
