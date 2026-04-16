# Automated Versioning and Release Workflow

This document describes the automated release workflow for the `generate-repo-file-list` GitHub Action.

## Overview

The action uses semantic versioning (`v1.2.3`) and automatically creates releases when changes are pushed to the `main` branch.

## How It Works

### 1. Version Detection

The workflow examines your commit messages since the last release to determine the version bump:

| Commit Pattern | Version Bump | Example |
| --- | --- | --- |
| `BREAKING CHANGE` or `!:` | **Major** | `v1.0.0` → `v2.0.0` |
| `feat:` or `feature:` | **Minor** | `v1.0.0` → `v1.1.0` |
| All others (fix, docs, etc.) | **Patch** | `v1.0.0` → `v1.0.1` |

### 2. Automatic Tagging

When you push to `main`:

1. The workflow calculates the next version
2. Creates a new version tag (e.g., `v1.2.3`)
3. Updates the major version tag (e.g., `v1`) to point to the latest release
4. Generates a changelog from commit messages
5. Creates a GitHub Release with the changelog

### 3. Tag Strategy

The workflow maintains two types of tags:

- **Specific version tags** (`v1.2.3`, `v1.2.4`, etc.) - immutable, pinned releases
- **Major version tags** (`v1`, `v2`, etc.) - updated to point to the latest minor/patch

## Usage in Other Repositories

### Recommended: Use Major Version Tag

This automatically gets bug fixes and new features (non-breaking):

```yaml
- uses: nick2bad4u/generate-repo-file-list@v1
  with:
   directory: "."
```

### Alternative: Pin to Specific Version

For maximum stability, pin to a specific release:

```yaml
- uses: nick2bad4u/generate-repo-file-list@v1.2.3
  with:
   directory: "."
```

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) for proper versioning:

### Patch Release (Bug Fixes)

```bash
git commit -m "fix: correct file path handling on Windows"
git commit -m "docs: update README with new examples"
git commit -m "chore: update dependencies"
```

### Minor Release (New Features)

```bash
git commit -m "feat: add support for custom file categories"
git commit -m "feature: implement lazy loading for large repos"
```

### Major Release (Breaking Changes)

```bash
git commit -m "feat!: restructure action inputs

BREAKING CHANGE: The 'file-list' input has been renamed to 'output-file'"
```

Or:

```bash
git commit -m "refactor: change API structure

BREAKING CHANGE: action now requires Python 3.11+"
```

## Workflow Configuration

The auto-release workflow is triggered on every push to `main`, except for:

- Changes to `*.md` files
- Changes to `LICENSE`
- Changes to `.gitignore`
- Changes to workflow files themselves

To disable auto-release, delete or disable `.github/workflows/auto-release.yml`.

## Manual Release Override

If you need to create a release manually:

```bash
# Create and push a tag manually
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# Create a GitHub release
gh release create v1.2.3 --title "v1.2.3" --notes "Release notes here"

# Update major version tag
git tag -f v1
git push origin v1 --force
```

## First Release

The workflow will create `v1.0.0` as the first semantic version tag when you push to `main`.

## Troubleshooting

### Release Not Created

Check that:

1. You pushed to the `main` branch
2. Your changes aren't only documentation/config files (see `paths-ignore`)
3. The workflow has `contents: write` permission
4. No errors in the Actions tab

### Wrong Version Bump

The workflow analyzes commit messages. Ensure:

1. Commit messages follow the conventional format
2. Use `feat:` for new features
3. Use `BREAKING CHANGE:` or `!:` for breaking changes
4. Other commits default to patch bumps

## Migration from Old Tags

Old tags (`github-action-published-final`, etc.) are preserved but won't affect new semantic versioning. The workflow starts from `v1.0.0` if no `v*.*.*` tags exist.
