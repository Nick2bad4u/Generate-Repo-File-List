"""TTS narration via Kokoro (default) or Google Cloud Text-to-Speech.

Why Kokoro by default:
- Local, free, no API key, deterministic
- Same engine the upstream training-video-generator uses (generate_kokoro.py)
- Quality is good enough for a Phase 0 spike

Switch to Google Cloud TTS by setting TTS_ENGINE=gcloud. Better voices, paid.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TTSClient:
    engine: str = ""

    def __post_init__(self) -> None:
        self.engine = self.engine or os.environ.get("TTS_ENGINE", "kokoro")
        if self.engine not in {"kokoro", "gcloud"}:
            raise ValueError(f"Unsupported TTS_ENGINE: {self.engine}")

    def synthesize(self, text: str, output_path: Path, voice: str | None = None) -> Path:
        """Synthesize text to a wav/mp3 file at output_path. Returns the path."""
        if self.engine == "kokoro":
            return self._kokoro(text, output_path, voice)
        return self._gcloud(text, output_path, voice)

    def _kokoro(self, text: str, output_path: Path, voice: str | None) -> Path:
        """Local Kokoro TTS via kokoro-onnx.

        Install: pip install kokoro-onnx soundfile
        Models auto-download on first call.
        """
        try:
            from kokoro_onnx import Kokoro
            import soundfile as sf
        except ImportError as e:
            raise RuntimeError(
                "Kokoro deps missing. Run: pip install kokoro-onnx soundfile"
            ) from e

        # Default voice; check kokoro-onnx docs for the full list
        voice = voice or "af_sarah"
        kokoro = Kokoro.from_pretrained()
        samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), samples, sample_rate)
        return output_path

    def _gcloud(self, text: str, output_path: Path, voice: str | None) -> Path:
        """Google Cloud Text-to-Speech.

        Uses Application Default Credentials (gcloud auth application-default login).
        """
        try:
            from google.cloud import texttospeech
        except ImportError as e:
            raise RuntimeError(
                "Google Cloud TTS deps missing. Run: pip install google-cloud-texttospeech"
            ) from e

        voice_name = voice or "en-US-Studio-O"  # natural female; swap as needed
        language = voice_name.split("-")[0] + "-" + voice_name.split("-")[1]

        client = texttospeech.TextToSpeechClient()
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code=language, name=voice_name
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
            ),
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.audio_content)
        return output_path
