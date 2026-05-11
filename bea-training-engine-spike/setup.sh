#!/usr/bin/env bash
#
# BEA Training Engine — Phase 0 Spike Setup
#
# Bootstraps the spike kit:
#   - Verifies python3 + gcloud are present
#   - Clones training-video-generator (NotebookLM Enterprise needs no fork)
#   - Creates a Python venv and installs deps
# Idempotent: safe to re-run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_MIN_VERSION="3.11"
VIDEO_GEN_FORK="https://github.com/BEA-BOLD-EVOLUTION/training-video-generator.git"
LEGACY_NOTEBOOKLM_FORK="https://github.com/BEA-BOLD-EVOLUTION/notebooklm-py.git"

# ---- helpers ----

log() { printf "\n\033[1;34m[spike-setup]\033[0m %s\n" "$*"; }
warn() { printf "\n\033[1;33m[spike-setup]\033[0m %s\n" "$*"; }
fail() { printf "\n\033[1;31m[spike-setup] ERROR:\033[0m %s\n" "$*" >&2; exit 1; }

check_python() {
  command -v python3 >/dev/null 2>&1 || fail "python3 not found. Install ${PYTHON_MIN_VERSION}+ first."
  local version
  version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" \
    || fail "Python ${version} found, but ${PYTHON_MIN_VERSION}+ required."
  log "Python ${version} OK"
}

check_ffmpeg() {
  if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
    warn "ffmpeg / ffprobe not found — required by video_renderer.py."
    warn "Install: brew install ffmpeg (macOS) | apt install ffmpeg (Linux)"
    warn "Continuing setup, but render-video will fail until ffmpeg is installed."
    return 0
  fi
  log "ffmpeg OK ($(ffmpeg -version | head -n 1))"
}

check_gcloud() {
  if ! command -v gcloud >/dev/null 2>&1; then
    warn "gcloud CLI not found."
    warn "Install: https://cloud.google.com/sdk/docs/install"
    warn "Then: gcloud auth login && gcloud auth application-default login"
    warn "Continuing setup, but the Enterprise API calls will fail until gcloud is installed."
    return 0
  fi
  log "gcloud OK ($(gcloud --version | head -n 1))"

  # Test that we can actually mint a token. If not, prompt the user but don't fail.
  if gcloud auth print-access-token >/dev/null 2>&1; then
    log "gcloud auth token OK"
  else
    warn "gcloud is installed but no active credential found."
    warn "Run: gcloud auth login"
  fi
}

clone_fork() {
  local url="$1"
  local dir="$2"
  if [[ -d "$dir" ]]; then
    log "Already cloned at ${dir}"
  else
    log "Cloning ${url} -> ${dir}"
    git clone "$url" "$dir"
  fi
}

# ---- main ----

log "Phase 0 spike setup starting in $(pwd)"

check_python
check_gcloud
check_ffmpeg

mkdir -p forks inputs outputs

# Always clone the video generator fork
clone_fork "$VIDEO_GEN_FORK" "forks/training-video-generator"

# Optionally clone the unofficial notebooklm-py if user opted into legacy mode
if [[ "${USE_LEGACY_NOTEBOOKLM:-false}" == "true" ]]; then
  log "USE_LEGACY_NOTEBOOKLM=true — also cloning the unofficial fork"
  clone_fork "$LEGACY_NOTEBOOKLM_FORK" "forks/notebooklm-py"
fi

# Bootstrap venv
if [[ ! -d ".venv" ]]; then
  log "Creating Python venv at .venv"
  python3 -m venv .venv
else
  log "venv already exists at .venv"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

log "Upgrading pip"
pip install --quiet --upgrade pip

log "Installing spike requirements"
pip install --quiet -r requirements.txt

# training-video-generator install
if [[ -f "forks/training-video-generator/pyproject.toml" || -f "forks/training-video-generator/setup.py" ]]; then
  log "Installing training-video-generator in editable mode"
  pip install --quiet -e forks/training-video-generator || warn "training-video-generator editable install failed; read its README"
elif [[ -f "forks/training-video-generator/requirements.txt" ]]; then
  log "Installing training-video-generator requirements"
  pip install --quiet -r forks/training-video-generator/requirements.txt || warn "Requirements install failed; read the fork's README"
else
  warn "training-video-generator has no installable manifest; read forks/training-video-generator/README.md"
fi

# Copy env template if missing
if [[ ! -f ".env" ]]; then
  log "Copying .env.example -> .env (edit it with real values before running the orchestrator)"
  cp .env.example .env
fi

log "Setup complete."
echo
echo "Next steps:"
echo "  1. Edit .env (GCP_PROJECT_NUMBER, NOTEBOOKLM_LOCATION, ANTHROPIC_API_KEY)"
echo "  2. Run: gcloud auth login && gcloud auth application-default login"
echo "  3. Confirm NotebookLM Enterprise license is enabled on your GCP project"
echo "  4. source .venv/bin/activate"
echo "  5. Place source docs in inputs/"
echo "  6. Place brand assets per brand/README.md"
echo "  7. Run: python src/spike_orchestrator.py auth"
