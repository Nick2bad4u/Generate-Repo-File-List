#!/usr/bin/env python3
"""Generate rich HTML or Markdown file indexes for repositories."""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import random
import subprocess
import sys
import textwrap
import urllib.parse
from dataclasses import dataclass, field
from itertools import cycle
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from tqdm import tqdm

TRUE_STRINGS = {"1", "true", "yes", "on"}
FALSE_STRINGS = {"0", "false", "no", "off"}

DEFAULT_FALLBACK_REPO_URL = "https://github.com/author/repo"
DEFAULT_IGNORE_LIST = [
    ".git",
    "node_modules",
    ".DS_Store",
    ".history",
    "styles",
    "zwiftbikes",
    "__pycache__",
    ".pytest_cache",
]
DEFAULT_OUTPUT_FORMAT = "html"
DEFAULT_OUTPUT_FILE = "file_list.html"
DEFAULT_HEADER_TEXT = "## File List"
DEFAULT_INTRO_TEXT = "# Here is a list of files included in this repository:"
DEFAULT_REPO_ROOT_HEADER = "Repo Root"
DEFAULT_COLOR_SOURCE = "random"
DEFAULT_COLOR_LIST = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
DEFAULT_COLOR_RANGE = ("#000000", "#FFFFFF")
DEFAULT_MAX_ATTEMPTS = 1_000_000
DEFAULT_DARK_LUMINANCE_THRESHOLD = 128
DEFAULT_BRIGHT_LUMINANCE_THRESHOLD = 200
DEFAULT_CHUNK_SIZE = 40
DEFAULT_VIEWPORT_MOBILE = 768
DEFAULT_VIEWPORT_TABLET = 1024
DEFAULT_VIEWPORT_SMALL_DESKTOP = 1440
DEFAULT_ROOT_MARGIN_MOBILE = "0px 0px 100px 0px"
DEFAULT_ROOT_MARGIN_TABLET = "0px 0px 200px 0px"
DEFAULT_ROOT_MARGIN_SMALL_DESKTOP = "0px 0px 300px 0px"
DEFAULT_ROOT_MARGIN_LARGE_DESKTOP = "0px 0px 400px 0px"
DEFAULT_LINK_REFERENCE = "main"
DEFAULT_GTM_ID = "GTM-T8J6HPLF"

DEFAULT_FILE_CATEGORIES_RAW = [
    (".user.css", "Userstyles"),
    (".user.js", "Userscripts"),
    (".css", "CSS"),
    (".js", "JavaScript"),
    (".yml", "YAML"),
]


@dataclass
class Category:
    ext: str
    name: str


@dataclass
class ColorPreferences:
    source: str
    colors: List[str]
    color_range: Tuple[str, str]
    max_attempts: int
    exclude_dark: bool
    exclude_bright: bool
    exclude_blacks: bool
    exclude_blacks_threshold: str
    ensure_readable: bool
    dark_luminance_threshold: int
    bright_luminance_threshold: int


@dataclass
class LazyLoadPreferences:
    chunk_size: int
    viewport_mobile: int
    viewport_tablet: int
    viewport_small_desktop: int
    root_margin_mobile: str
    root_margin_tablet: str
    root_margin_small_desktop: str
    root_margin_large_desktop: str


@dataclass
class GeneratorConfig:
    directory: Path
    repo_url: Optional[str]
    fallback_repo_url: Optional[str]
    link_reference: str
    output_format: str
    output_file: Optional[Path]
    header_text: str
    intro_text: str
    repo_root_header: str
    categories: List[Category]
    ignore_list: List[str]
    color: ColorPreferences
    lazy: LazyLoadPreferences
    respect_gitignore: bool
    log_level: str
    gtm_id: str


def str_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    lowered = value.strip().lower()
    if lowered in TRUE_STRINGS:
        return True
    if lowered in FALSE_STRINGS:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, received '{value}'.")


def normalize_hex_color(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("Color value cannot be empty.")
    if not candidate.startswith("#"):
        candidate = f"#{candidate}"
    if len(candidate) != 7:
        raise ValueError("Color values must be in the format #RRGGBB.")
    try:
        int(candidate[1:], 16)
    except ValueError as exc:
        raise ValueError(f"Color '{value}' is not a valid hex code.") from exc
    return candidate.upper()


def sort_color_range(low: str, high: str) -> Tuple[str, str]:
    low_norm = normalize_hex_color(low)
    high_norm = normalize_hex_color(high)
    if int(low_norm[1:], 16) <= int(high_norm[1:], 16):
        return low_norm, high_norm
    return high_norm, low_norm


def calculate_luminance(color: str) -> float:
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def is_black_color(color: str, threshold: str) -> bool:
    return int(color[1:], 16) <= int(threshold[1:], 16)


class ColorGenerator:
    def __init__(self, prefs: ColorPreferences) -> None:
        self.prefs = prefs
        if prefs.source == "list":
            if not prefs.colors:
                raise ValueError("Color list cannot be empty when color-source is 'list'.")
            self._list_cycle = cycle(prefs.colors)
        else:
            self._list_cycle = None
        low, high = prefs.color_range
        self._range_low = tuple(int(low[i : i + 2], 16) for i in (1, 3, 5))
        self._range_high = tuple(int(high[i : i + 2], 16) for i in (1, 3, 5))

    def next_color(self) -> str:
        if self._list_cycle is not None:
            return next(self._list_cycle)
        for _ in range(self.prefs.max_attempts):
            r = random.randint(self._range_low[0], self._range_high[0])
            g = random.randint(self._range_low[1], self._range_high[1])
            b = random.randint(self._range_low[2], self._range_high[2])
            candidate = f"#{r:02X}{g:02X}{b:02X}"
            if not self._should_exclude(candidate):
                return candidate
        logging.warning(
            "Failed to generate a colour meeting the constraints after %s attempts; falling back to unrestricted colour.",
            self.prefs.max_attempts,
        )
        return f"#{random.randint(0, 0xFFFFFF):06X}"

    def _should_exclude(self, color: str) -> bool:
        luminance: Optional[float] = None
        if self.prefs.exclude_dark or self.prefs.exclude_bright or self.prefs.ensure_readable:
            luminance = calculate_luminance(color)
        if self.prefs.exclude_dark and luminance is not None and luminance < self.prefs.dark_luminance_threshold:
            return True
        if self.prefs.exclude_bright and luminance is not None and luminance > self.prefs.bright_luminance_threshold:
            return True
        if self.prefs.exclude_blacks and is_black_color(color, self.prefs.exclude_blacks_threshold):
            return True
        if self.prefs.ensure_readable and luminance is not None and not (50 < luminance < 200):
            return True
        return False


def should_ignore(path: Path, ignore_list: Sequence[str]) -> bool:
    parts = [part for part in path.parts if part not in ("", ".")]
    for ignore in ignore_list:
        item = ignore.strip()
        if not item:
            continue
        if item in parts:
            return True
    return False


def collect_via_os(root: Path, ignore_list: Sequence[str]) -> List[Path]:
    collected: List[Path] = []
    walker = os.walk(root)
    show_progress = logging.getLogger().isEnabledFor(logging.INFO) and sys.stderr.isatty()
    iterator = tqdm(walker, desc="Walking through directories", disable=not show_progress)
    for current_root, dirs, files in iterator:
        relative_root = Path(current_root).relative_to(root)
        dirs[:] = [
            d
            for d in dirs
            if not should_ignore((relative_root / d) if relative_root != Path(".") else Path(d), ignore_list)
        ]
        for file_name in files:
            rel_path = (relative_root / file_name) if relative_root != Path(".") else Path(file_name)
            if should_ignore(rel_path, ignore_list):
                continue
            collected.append(rel_path)
    collected.sort(key=lambda path: path.as_posix().lower())
    return collected


def collect_via_git(root: Path, ignore_list: Sequence[str]) -> Optional[List[Path]]:
    try:
        repo_root = (
            subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        logging.debug("Unable to determine git repository root: %s", exc)
        return None
    repo_root_path = Path(repo_root).resolve()
    try:
        root.relative_to(repo_root_path)
    except ValueError:
        logging.debug("Directory '%s' is not contained within git root '%s'", root, repo_root_path)
        return None
    try:
        ls_output = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=repo_root_path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        logging.debug("git ls-files failed: %s", exc)
        return None
    files: List[Path] = []
    for line in ls_output.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        repo_relative = Path(candidate)
        abs_path = (repo_root_path / repo_relative).resolve()
        try:
            rel_to_target = abs_path.relative_to(root)
        except ValueError:
            continue
        if rel_to_target == Path(".") or should_ignore(rel_to_target, ignore_list):
            continue
        files.append(rel_to_target)
    files.sort(key=lambda path: path.as_posix().lower())
    logging.debug("Collected %d files via git ls-files", len(files))
    return files


def collect_files(config: GeneratorConfig) -> List[Path]:
    if config.respect_gitignore:
        git_files = collect_via_git(config.directory, config.ignore_list)
        if git_files is not None:
            return git_files
        logging.info("Falling back to filesystem traversal; git-aware discovery unavailable.")
    return collect_via_os(config.directory, config.ignore_list)


def normalize_repo_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    candidate = url.strip()
    if not candidate:
        return None
    if candidate.startswith("git@") and ":" in candidate:
        user_host, path = candidate.split(":", 1)
        host = user_host.split("@", 1)[1]
        candidate = f"https://{host}/{path}"
    if candidate.startswith("ssh://"):
        candidate = candidate.replace("ssh://", "https://", 1)
        candidate = candidate.replace("git@", "", 1)
    candidate = candidate.rstrip("/")
    if candidate.endswith(".git"):
        candidate = candidate[:-4]
    return candidate


def resolve_repo_url(provided: Optional[str], fallback: Optional[str], directory: Path) -> Optional[str]:
    explicit = normalize_repo_url(provided)
    if explicit:
        return explicit
    env_repo = os.getenv("GITHUB_REPOSITORY")
    if env_repo:
        env_url = normalize_repo_url(f"https://github.com/{env_repo}")
        if env_url:
            return env_url
    try:
        remote_url = (
            subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        remote_url = ""
    normalized_remote = normalize_repo_url(remote_url)
    if normalized_remote:
        return normalized_remote
    fallback_url = normalize_repo_url(fallback)
    if fallback_url:
        return fallback_url
    return normalize_repo_url(DEFAULT_FALLBACK_REPO_URL)


def resolve_default_branch(provided: Optional[str], directory: Path) -> str:
    if provided and provided.strip():
        return provided.strip()
    env_branch = os.getenv("GITHUB_REF_NAME") or os.getenv("GITHUB_HEAD_REF")
    if env_branch:
        return env_branch
    try:
        branch = (
            subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )
        if branch:
            return branch
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    return DEFAULT_LINK_REFERENCE


def resolve_link_reference(link_ref: Optional[str], default_branch: Optional[str], directory: Path) -> str:
    if link_ref and link_ref.strip():
        return link_ref.strip()
    return resolve_default_branch(default_branch, directory)


def build_file_url(repo_url: Optional[str], link_reference: str, relative_path: str) -> str:
    encoded_path = urllib.parse.quote(relative_path, safe="/")
    if not repo_url:
        return encoded_path
    base = repo_url.rstrip("/")
    return f"{base}/blob/{link_reference}/{encoded_path}"


def build_sections(files: Sequence[Path], categories: Sequence[Category], repo_root_header: str) -> List[Tuple[str, List[str]]]:
    root_files: List[str] = []
    category_map: Dict[str, List[str]] = {category.name: [] for category in categories}
    other_folders: Dict[str, List[str]] = {}
    for path in files:
        posix = path.as_posix()
        lower = posix.lower()
        matched = False
        for category in categories:
            if lower.endswith(category.ext.lower()):
                category_map[category.name].append(posix)
                matched = True
                break
        if matched:
            continue
        if "/" in posix:
            folder = posix.rsplit("/", 1)[0]
            other_folders.setdefault(folder, []).append(posix)
        else:
            root_files.append(posix)
    root_files.sort()
    for entries in category_map.values():
        entries.sort()
    for entries in other_folders.values():
        entries.sort()
    sections: List[Tuple[str, List[str]]] = []
    if root_files:
        sections.append((repo_root_header, root_files))
    for category in categories:
        entries = category_map[category.name]
        if entries:
            sections.append((category.name, entries))
    for folder in sorted(other_folders.keys(), key=lambda item: item.lower()):
        sections.append((folder, other_folders[folder]))
    return sections


def build_lazyload_script(lazy: LazyLoadPreferences, chunk_data: Dict[str, str]) -> str:
    viewport_rules = [
        {
            "maxWidth": lazy.viewport_mobile,
            "rootMargin": lazy.root_margin_mobile,
            "threshold": 0.1,
        },
        {
            "maxWidth": lazy.viewport_tablet,
            "rootMargin": lazy.root_margin_tablet,
            "threshold": 0.3,
        },
        {
            "maxWidth": lazy.viewport_small_desktop,
            "rootMargin": lazy.root_margin_small_desktop,
            "threshold": 0.4,
        },
        {
            "maxWidth": None,
            "rootMargin": lazy.root_margin_large_desktop,
            "threshold": 0.5,
        },
    ]
    script = textwrap.dedent(
        f"""
        <script>
        document.addEventListener("DOMContentLoaded", function() {{
          const chunkData = {json.dumps(chunk_data)};
          const lazyLoadElements = document.querySelectorAll(".lazyload-placeholder");
          if (!lazyLoadElements.length) {{
            return;
          }}
          const viewportRules = {json.dumps(viewport_rules)};
          function pickObserverConfig(width) {{
            for (const rule of viewportRules) {{
              if (rule.maxWidth === null || width <= rule.maxWidth) {{
                return rule;
              }}
            }}
            return viewportRules[viewportRules.length - 1];
          }}
          const width = window.innerWidth || document.documentElement.clientWidth || 0;
          const currentConfig = pickObserverConfig(width);
          if ("IntersectionObserver" in window) {{
            const observer = new IntersectionObserver((entries, obs) => {{
              entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                  const placeholder = entry.target;
                  const key = placeholder.dataset.content;
                  if (chunkData[key]) {{
                    placeholder.innerHTML = chunkData[key];
                  }}
                  obs.unobserve(placeholder);
                }}
              }});
            }}, {{ rootMargin: currentConfig.rootMargin, threshold: currentConfig.threshold }});
            lazyLoadElements.forEach(element => observer.observe(element));
          }} else {{
            lazyLoadElements.forEach(placeholder => {{
              const key = placeholder.dataset.content;
              if (chunkData[key]) {{
                placeholder.innerHTML = chunkData[key];
              }}
            }});
          }}
        }});
        </script>
        """
    ).strip()
    return script


def render_html(files: Sequence[Path], config: GeneratorConfig) -> str:
    sections = build_sections(files, config.categories, config.repo_root_header)
    color_gen = ColorGenerator(config.color)
    header_text = config.header_text.strip().lstrip("#").strip() or "Repository File List"
    intro_text = config.intro_text.strip().lstrip("#").strip()
    repo_link = config.repo_url or "#"
    gtm_head = ""
    gtm_body = ""

    if config.gtm_id:
        gtm_head = textwrap.dedent(
            f"""
            <!-- Google Tag Manager -->
            <script>
            (function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start': new Date().getTime(),event:'gtm.js'}});
            var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
            'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
            }})(window,document,'script','dataLayer','{config.gtm_id}');
            </script>
            <!-- End Google Tag Manager -->
            """
        ).strip()
        gtm_body = (
            f'<!-- Google Tag Manager (noscript) --><noscript><iframe src="https://www.googletagmanager.com/ns.html?id={config.gtm_id}" '
            'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript><!-- End Google Tag Manager (noscript) -->'
        )

    content_parts: List[str] = []
    content_parts.append(
        textwrap.dedent(
            f"""
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>{html.escape(header_text)} • {html.escape(config.directory.name)}</title>
              <meta name="description" content="Beautiful, lazy-loaded repository file list." />
              {gtm_head}
              <style>
                :root {{
                  --bg: #0b1020;
                  --surface: #141a2f;
                  --surface-2: #1a2340;
                  --text: #e8ecff;
                  --muted: #b7c0ea;
                  --accent: #6ea8fe;
                  --border: #2a355f;
                }}
                * {{ box-sizing: border-box; }}
                body {{
                  margin: 0;
                  font-family: Inter, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
                  background: radial-gradient(circle at top, #18274d 0%, var(--bg) 45%);
                  color: var(--text);
                  line-height: 1.6;
                }}
                .wrap {{ max-width: 1100px; margin: 0 auto; padding: 32px 16px 48px; }}
                .hero {{
                  background: linear-gradient(160deg, rgba(110,168,254,.15), rgba(74,144,226,.05));
                  border: 1px solid var(--border);
                  border-radius: 16px;
                  padding: 24px;
                  margin-bottom: 18px;
                }}
                h1 {{ margin: 0 0 8px; font-size: clamp(1.7rem, 2.8vw, 2.3rem); }}
                .subtitle {{ margin: 0; color: var(--muted); }}
                .meta {{
                  margin-top: 14px;
                  display: flex;
                  flex-wrap: wrap;
                  gap: 10px;
                }}
                .pill {{
                  display: inline-flex;
                  align-items: center;
                  gap: 8px;
                  border: 1px solid var(--border);
                  background: rgba(20, 26, 47, .75);
                  border-radius: 999px;
                  padding: 6px 12px;
                  font-size: .88rem;
                  color: var(--muted);
                }}
                .card {{
                  background: var(--surface);
                  border: 1px solid var(--border);
                  border-radius: 14px;
                  padding: 16px;
                }}
                .card ul {{ margin: 0; padding: 0; list-style: none; }}
                .card li {{ margin: 0; }}
                .card h2 {{
                  margin: 18px 0 8px;
                  font-size: 1.05rem;
                }}
                .card li:first-child h2 {{ margin-top: 6px; }}
                .card a {{
                  text-decoration: none;
                  font-weight: 500;
                  word-break: break-word;
                }}
                .card a:hover {{ text-decoration: underline; }}
                .toolbar {{
                  display: flex;
                  flex-wrap: wrap;
                  gap: 10px;
                  margin-bottom: 12px;
                }}
                .btn {{
                  background: var(--surface-2);
                  border: 1px solid var(--border);
                  color: var(--text);
                  text-decoration: none;
                  border-radius: 10px;
                  padding: 8px 12px;
                  font-size: .9rem;
                }}
                .btn:hover {{ border-color: var(--accent); }}
                footer {{ color: var(--muted); margin-top: 16px; font-size: .85rem; }}
              </style>
            </head>
            <body>
              {gtm_body}
              <main class="wrap">
                <section class="hero">
                  <h1>{html.escape(header_text)}</h1>
                  <p class="subtitle">{html.escape(intro_text or 'Explore every file in this repository with fast lazy loading.')}</p>
                  <div class="meta">
                    <span class="pill">📁 {len(files)} files</span>
                    <span class="pill">🏷️ Ref: {html.escape(config.link_reference)}</span>
                    <a class="pill" href="{html.escape(repo_link)}" target="_blank" rel="noopener">🔗 Repository</a>
                  </div>
                </section>
                <section class="card">
                  <div class="toolbar">
                    <a class="btn" href="./README.md" target="_blank" rel="noopener">README</a>
                    <a class="btn" href="./file_list.md" target="_blank" rel="noopener">Markdown View</a>
                    <a class="btn" href="{html.escape(repo_link)}" target="_blank" rel="noopener">Open on GitHub</a>
                  </div>
            """
        ).strip()
    )

    body_lines: List[str] = []
    for title, entries in sections:
        header_color = color_gen.next_color()
        body_lines.append(f'<li><h2 style="color: {header_color};">{html.escape(title)}</h2></li>')
        for entry in entries:
            color = color_gen.next_color()
            url = build_file_url(config.repo_url, config.link_reference, entry)
            body_lines.append(
                f'<li><a href="{url}" style="color: {color};">{html.escape(entry)}</a></li>'
            )

    if not body_lines:
        content_parts.append("<p>No files found.</p>")
        content_parts.append("</section><footer>Generated by generate-repo-file-list.</footer></main></body></html>")
        return "\n\n".join(content_parts).strip() + "\n"

    chunk_size = max(1, config.lazy.chunk_size)
    chunks = [
        "\n".join(body_lines[index : index + chunk_size])
        for index in range(0, len(body_lines), chunk_size)
    ]
    chunk_map = {f"file-list-{idx + 1}": f"<ul>{chunk}</ul>" for idx, chunk in enumerate(chunks)}
    placeholders = "\n".join(
        f'<div class="lazyload-placeholder" data-content="file-list-{idx + 1}" style="min-height: 400px;"></div>'
        for idx in range(len(chunks))
    )
    content_parts.append(placeholders)
    content_parts.append(build_lazyload_script(config.lazy, chunk_map))
    content_parts.append("</section><footer>Generated by generate-repo-file-list.</footer></main></body></html>")
    return "\n\n".join(content_parts).strip() + "\n"


def render_markdown(files: Sequence[Path], config: GeneratorConfig) -> str:
    sections = build_sections(files, config.categories, config.repo_root_header)
    lines: List[str] = []

    header_text = config.header_text.strip()
    if header_text:
        if header_text.startswith("#"):
            lines.append(header_text)
        else:
            lines.append(f"## {header_text}")
        lines.append("")

    intro_text = config.intro_text.strip()
    if intro_text:
        lines.append(intro_text)
        lines.append("")

    for title, entries in sections:
        cleaned_title = title.strip()
        if cleaned_title:
            if cleaned_title.startswith("#"):
                lines.append(cleaned_title)
            else:
                lines.append(f"### {cleaned_title}")
            lines.append("")
        for entry in entries:
            url = build_file_url(config.repo_url, config.link_reference, entry)
            lines.append(f"- [{html.escape(entry)}]({url})")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate colourful HTML or Markdown file indexes for repositories.")
    parser.add_argument("--directory", default=".", help="Root directory to scan.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    parser.add_argument("--repo-url", help="Primary repository URL for generated links.")
    parser.add_argument("--fallback-repo-url", default=DEFAULT_FALLBACK_REPO_URL, help="Fallback repository URL when automatic detection fails.")
    parser.add_argument("--output-format", choices=["html", "markdown"], default=DEFAULT_OUTPUT_FORMAT)
    parser.add_argument("--output-file", default=DEFAULT_OUTPUT_FILE, help="Destination file name. Use '-' to write to stdout.")
    parser.add_argument("--color-source", choices=["random", "list"], default=DEFAULT_COLOR_SOURCE)
    parser.add_argument("--color-list", nargs="+", help="Colour list when using color-source=list (hex codes).")
    parser.add_argument("--color-range", nargs=2, metavar=("MIN", "MAX"), help="Random colour range bounds (#RRGGBB).")
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS, help="Maximum attempts when searching for compliant colours.")
    parser.add_argument("--exclude-dark-colors", nargs="?", const=True, default=False, type=str_to_bool, help="Exclude colours below the dark luminance threshold.")
    parser.add_argument("--exclude-bright-colors", nargs="?", const=True, default=False, type=str_to_bool, help="Exclude colours above the bright luminance threshold.")
    parser.add_argument("--exclude-blacks", nargs="?", const=True, default=False, type=str_to_bool, help="Exclude colours darker than the black threshold.")
    parser.add_argument("--exclude-blacks-threshold", default="#222222", help="Hex threshold for classifying blacks.")
    parser.add_argument("--ensure-readable-colors", nargs="?", const=True, default=False, type=str_to_bool, help="Keep colours within a readable luminance band.")
    parser.add_argument("--dark-color-luminance-threshold", type=int, default=DEFAULT_DARK_LUMINANCE_THRESHOLD)
    parser.add_argument("--bright-color-luminance-threshold", type=int, default=DEFAULT_BRIGHT_LUMINANCE_THRESHOLD)
    parser.add_argument("--repo-root-header", default=DEFAULT_REPO_ROOT_HEADER)
    parser.add_argument("--header-text", default=DEFAULT_HEADER_TEXT)
    parser.add_argument("--intro-text", default=DEFAULT_INTRO_TEXT)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--viewport-mobile", type=int, default=DEFAULT_VIEWPORT_MOBILE)
    parser.add_argument("--viewport-tablet", type=int, default=DEFAULT_VIEWPORT_TABLET)
    parser.add_argument("--viewport-small-desktop", type=int, default=DEFAULT_VIEWPORT_SMALL_DESKTOP)
    parser.add_argument("--root-margin-mobile", default=DEFAULT_ROOT_MARGIN_MOBILE)
    parser.add_argument("--root-margin-tablet", default=DEFAULT_ROOT_MARGIN_TABLET)
    parser.add_argument("--root-margin-small-desktop", default=DEFAULT_ROOT_MARGIN_SMALL_DESKTOP)
    parser.add_argument("--root-margin-large-desktop", default=DEFAULT_ROOT_MARGIN_LARGE_DESKTOP)
    parser.add_argument("--file-categories", nargs="+", help="Pairs of extension/name to append to the default category set.")
    parser.add_argument("--overwrite-file-categories", action="store_true", help="Replace the default categories instead of extending them.")
    parser.add_argument("--ignore-list", nargs="+", help="Additional entries to ignore during traversal.")
    parser.add_argument("--overwrite-ignore-list", action="store_true", help="Replace the default ignore list instead of extending it.")
    parser.add_argument("--respect-gitignore", nargs="?", const=True, default=False, type=str_to_bool, help="Prefer git ls-files so .gitignore rules are honoured.")
    parser.add_argument("--link-ref", help="Explicit branch, tag, or SHA to use when building links.")
    parser.add_argument("--default-branch", help="Fallback branch name when link-ref is not supplied.")
    parser.add_argument("--gtm-id", default=DEFAULT_GTM_ID, help="Google Tag Manager container ID to embed in generated HTML.")
    parser.add_argument("--output-file-stdout", dest="output_file_stdout", nargs="?", const=True, default=False, type=str_to_bool, help="Write output to stdout regardless of output-file value.")
    return parser


def build_config(args: argparse.Namespace) -> GeneratorConfig:
    directory = Path(args.directory).resolve()
    if not directory.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist.")
    color_list_values = args.color_list or DEFAULT_COLOR_LIST
    if isinstance(color_list_values, list) and len(color_list_values) == 1:
        single_value = color_list_values[0]
        if isinstance(single_value, str) and " " in single_value:
            color_list_values = [value for value in single_value.split() if value]
    try:
        color_list = [normalize_hex_color(value) for value in color_list_values]
    except ValueError as exc:
        raise ValueError(f"Invalid colour in color-list: {exc}")
    if args.color_range:
        try:
            color_range = sort_color_range(args.color_range[0], args.color_range[1])
        except ValueError as exc:
            raise ValueError(f"Invalid colour range: {exc}")
    else:
        color_range = DEFAULT_COLOR_RANGE
    try:
        exclude_blacks_threshold = normalize_hex_color(args.exclude_blacks_threshold)
    except ValueError as exc:
        raise ValueError(f"Invalid exclude-blacks-threshold: {exc}")
    categories = [Category(ext=ext, name=name) for ext, name in DEFAULT_FILE_CATEGORIES_RAW]
    file_categories_raw = args.file_categories
    if isinstance(file_categories_raw, list) and len(file_categories_raw) == 1:
        single_value = file_categories_raw[0]
        if isinstance(single_value, str) and " " in single_value:
            file_categories_raw = [value for value in single_value.split() if value]
    if file_categories_raw:
        file_categories_raw = [entry for entry in file_categories_raw if entry]
    if file_categories_raw:
        if len(file_categories_raw) % 2 != 0:
            raise ValueError("--file-categories expects EXT NAME pairs.")
        additional = [
            Category(ext=file_categories_raw[index], name=file_categories_raw[index + 1])
            for index in range(0, len(file_categories_raw), 2)
        ]
        if args.overwrite_file_categories:
            categories = additional
        else:
            categories.extend(additional)
    ignore_list_entries = args.ignore_list
    if isinstance(ignore_list_entries, list) and len(ignore_list_entries) == 1:
        single_value = ignore_list_entries[0]
        if isinstance(single_value, str) and " " in single_value:
            ignore_list_entries = [value for value in single_value.split() if value]
    if ignore_list_entries:
        ignore_list_entries = [entry for entry in ignore_list_entries if entry]
    ignore_list = list(DEFAULT_IGNORE_LIST)
    if args.overwrite_ignore_list:
        ignore_list = list(ignore_list_entries or [])
    elif ignore_list_entries:
        ignore_list.extend(ignore_list_entries)
    deduped_ignore: List[str] = []
    seen_ignore = set()
    for item in ignore_list:
        key = item.strip()
        if key and key not in seen_ignore:
            seen_ignore.add(key)
            deduped_ignore.append(key)
    ignore_list = deduped_ignore
    repo_url = resolve_repo_url(args.repo_url, args.fallback_repo_url, directory)
    link_reference = resolve_link_reference(args.link_ref, args.default_branch, directory)
    output_file_arg = args.output_file
    if args.output_format == "html" and output_file_arg.lower().endswith(".md"):
        output_file_arg = output_file_arg[:-3] + ".html"
    output_path: Optional[Path]
    if args.output_file_stdout or (output_file_arg.strip() == "-"):
        output_path = None
    else:
        candidate = Path(output_file_arg)
        if not candidate.is_absolute():
            candidate = (directory / candidate).resolve()
        output_path = candidate
    color_preferences = ColorPreferences(
        source=args.color_source,
        colors=color_list,
        color_range=color_range,
        max_attempts=max(args.max_attempts, 1),
        exclude_dark=args.exclude_dark_colors,
        exclude_bright=args.exclude_bright_colors,
        exclude_blacks=args.exclude_blacks,
        exclude_blacks_threshold=exclude_blacks_threshold,
        ensure_readable=args.ensure_readable_colors,
        dark_luminance_threshold=args.dark_color_luminance_threshold,
        bright_luminance_threshold=args.bright_color_luminance_threshold,
    )
    lazy_preferences = LazyLoadPreferences(
        chunk_size=max(1, args.chunk_size),
        viewport_mobile=args.viewport_mobile,
        viewport_tablet=args.viewport_tablet,
        viewport_small_desktop=args.viewport_small_desktop,
        root_margin_mobile=args.root_margin_mobile,
        root_margin_tablet=args.root_margin_tablet,
        root_margin_small_desktop=args.root_margin_small_desktop,
        root_margin_large_desktop=args.root_margin_large_desktop,
    )
    return GeneratorConfig(
        directory=directory,
        repo_url=repo_url,
        fallback_repo_url=normalize_repo_url(args.fallback_repo_url),
        link_reference=link_reference,
        output_format=args.output_format,
        output_file=output_path,
        header_text=args.header_text,
        intro_text=args.intro_text,
        repo_root_header=args.repo_root_header,
        categories=categories,
        ignore_list=ignore_list,
        color=color_preferences,
        lazy=lazy_preferences,
        respect_gitignore=args.respect_gitignore,
        log_level=args.log_level,
        gtm_id=(args.gtm_id or "").strip(),
    )


def write_output(config: GeneratorConfig, content: str) -> None:
    if config.output_file is None:
        sys.stdout.write(content)
        return
    config.output_file.parent.mkdir(parents=True, exist_ok=True)
    config.output_file.write_text(content, encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = build_config(args)
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
        return 1
    numeric_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.getLogger("tqdm").setLevel(logging.ERROR)
    logging.info("Scanning directory: %s", config.directory)
    logging.debug("Using repository URL: %s", config.repo_url)
    logging.debug("Link reference: %s", config.link_reference)
    files = collect_files(config)
    logging.info("Discovered %d files", len(files))
    if config.output_format == "html":
        content = render_html(files, config)
    else:
        content = render_markdown(files, config)
    write_output(config, content)
    logging.info(
        "Wrote file list to %s",
        "stdout" if config.output_file is None else config.output_file,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
