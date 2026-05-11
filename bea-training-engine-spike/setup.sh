#!/usr/bin/env bash
#
# BEA Training Engine — Phase 0 Spike Setup
#
# Clones the two key forks, bootstraps a Python venv, installs deps.
# Idempotent: safe to re-run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_MIN_VERSION="3.11"
NOTEBOOKLM_FORK="https://github.com/BEA-BOLD-EVOLUTION/notebooklm-py.git"
VIDEO_GEN_FORK="https://github.com/BEA-BOLD-EVOLUTION/training-video-generator.git"

# ---- helpers ----

log() { printf "\n\033[1;34m[spike-setup]\033[0m %s\n" "$*"; }
fail() { printf "\n\033[1;31m[spike-setup] ERROR:\033[0m %s\n" "$*" >&2; exit 1; }

check_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found. Install Python ${PYTHON_MIN_VERSION}+ first."
  fi
  local version
  version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
    fail "Python ${version} found, but ${PYTHON_MIN_VERSION}+ required."
  fi
  log "Python ${version} OK"
}

clone_fork() {
  local url="$1"
  local dir="$2"
  if [[ -d "$dir" ]]; then
    log "Fork already cloned at ${dir}, pulling latest"
    (cd "$dir" && git pull --ff-only) || log "Pull failed (probably diverged); leaving as-is"
  else
    log "Cloning ${url} -> ${dir}"
    git clone "$url" "$dir"
  fi
}

# ---- main ----

log "Phase 0 spike setup starting in $(pwd)"

check_python

# Create directory structure that's gitignored
mkdir -p forks inputs outputs

# Clone the two forks we'll exercise
clone_fork "$NOTEBOOKLM_FORK" "forks/notebooklm-py"
clone_fork "$VIDEO_GEN_FORK" "forks/training-video-generator"

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

# Install forks in editable mode (best-effort — they may not be pip packages)
if [[ -f "forks/notebooklm-py/pyproject.toml" || -f "forks/notebooklm-py/setup.py" ]]; then
  log "Installing notebooklm-py in editable mode"
  pip install --quiet -e forks/notebooklm-py || log "notebooklm-py editable install failed; you may need to import it differently — read its README"
else
  log "notebooklm-py has no setup.py/pyproject.toml; you'll import it directly. Read forks/notebooklm-py/README.md"
fi

if [[ -f "forks/training-video-generator/pyproject.toml" || -f "forks/training-video-generator/setup.py" ]]; then
  log "Installing training-video-generator in editable mode"
  pip install --quiet -e forks/training-video-generator || log "training-video-generator editable install failed; read its README"
elif [[ -f "forks/training-video-generator/requirements.txt" ]]; then
  log "Installing training-video-generator requirements"
  pip install --quiet -r forks/training-video-generator/requirements.txt || log "Requirements install failed; read the fork's README"
else
  log "training-video-generator has no installable manifest; read forks/training-video-generator/README.md"
fi

# Copy env template if missing
if [[ ! -f ".env" ]]; then
  log "Copying .env.example -> .env (edit it with real values before running the orchestrator)"
  cp .env.example .env
fi

log "Setup complete."
echo
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. source .venv/bin/activate"
echo "  3. Read forks/notebooklm-py/README.md to learn the auth method"
echo "  4. Place source docs in inputs/"
echo "  5. Place brand assets per brand/README.md"
echo "  6. Run: python src/spike_orchestrator.py auth"
