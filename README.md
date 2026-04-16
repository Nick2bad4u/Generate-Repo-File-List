<div align="center">

# 📂 Generate Repo File List

### 🚀 Automatically create beautiful, organized file indexes for your GitHub repositories

[![GitHub release](https://img.shields.io/github/v/release/Nick2bad4u/generate-repo-file-list?style=for-the-badge&logo=github)](https://github.com/Nick2bad4u/generate-repo-file-list/releases)
[![Tests](https://img.shields.io/github/actions/workflow/status/Nick2bad4u/generate-repo-file-list/main.yml?style=for-the-badge&label=tests)](https://github.com/Nick2bad4u/generate-repo-file-list/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg?style=for-the-badge)](https://unlicense.org)

---

**Transform your repository structure into beautifully formatted HTML or Markdown file listings with custom colors, lazy loading, and automatic README updates.**

[🎯 Features](#-features) • [🚀 Quick Start](#-quick-start) • [⚙️ Configuration](#️-configuration) • [📖 Examples](#-examples) • [🔄 Versioning](#-versioning-and-releases)

</div>

---

## ✨ Features

- 🎨 **Colorful Output** - Generate file lists with vibrant, customizable color schemes
- 📱 **Responsive Design** - Lazy loading optimized for mobile, tablet, and desktop viewports
- 🔄 **Auto README Updates** - Seamlessly inject file lists into your README using markers
- 🎯 **Smart Categorization** - Organize files by extension (Python, YAML, JavaScript, etc.)
- 🚫 **Gitignore Integration** - Respect `.gitignore` rules for clean file discovery
- 📊 **Dual Format Support** - Generate both HTML and Markdown outputs
- ⚡ **Performance Optimized** - Chunk-based rendering for large repositories
- 🔒 **Secure** - Hardened runner and comprehensive security best practices

---

## 🚀 Quick Start

### 📋 Prerequisites

Add these markers to your `README.md` where you want the file list to appear:

```markdown
<!-- FILE_LIST_START -->
<!-- FILE_LIST_END -->
```

### 🎬 Basic Workflow Setup

Create `.github/workflows/file-list.yml` in your repository:

```yaml
name: 📂 Generate File List

on:
 push:
  branches: [main]
 workflow_dispatch:

permissions:
 contents: write

jobs:
 generate-file-list:
  runs-on: ubuntu-latest

  steps:
   - name: 📥 Checkout repository
     uses: actions/checkout@v4

   - name: 🐍 Set up Python
     uses: actions/setup-python@v5
     with:
      python-version: "3.x"

   - name: 📂 Generate File List
     uses: nick2bad4u/generate-repo-file-list@v1
     with:
      directory: "."
      output-format: "markdown"
      output-file: "file_list.md"
      respect-gitignore: "true"

   - name: 💾 Commit Changes
     uses: stefanzweifel/git-auto-commit-action@v5
     with:
      commit_message: "📂 Update file list automatically"
```

> 💡 **Tip**: Remove the `cron` schedule if you only want manual/push-triggered runs.

---

## 📖 Advanced Workflow Example

<details>
<summary>🔧 Click to see full-featured workflow with all options</summary>

```yaml
name: Generate and Update README.MD File List

on:
 push:
  branches:
   - main
 pull_request:
  branches:
   - main
 workflow_dispatch: # Allows manual triggering

permissions:
 contents: write
 pull-requests: write

jobs:
 build:
  runs-on: ubuntu-latest

  steps:
   - name: Checkout repository
     uses: actions/checkout@v4

   - name: List files in the repository
     run: |
      ls -al

   - name: Verify README.md exists
     run: |
      if [ ! -f README.md ]; then
        echo "README.md not found!"
        exit 1
      fi

   - name: Set up Python
     uses: actions/setup-python@v5
     with:
      python-version: "3.x"

   - name: Create src directory
     run: mkdir -p src

   - name: Download generate_file_list.py
     run: |
      curl -L -o src/generate_file_list.py https://github.com/Nick2bad4u/generate-repo-file-list/raw/refs/heads/main/src/generate_file_list.py
      chmod +x src/generate_file_list.py

   - name: Install dependencies (if any)
     run: |
      python -m pip install tqdm==4.66.4
      # Add any dependencies your script needs here
      # For example: pip install requests

   - name: Run Generate Repo File List Action
     uses: nick2bad4u/generate-repo-file-list@main
     with:
      log-level: "INFO"
      directory: "."
      repo-url: "https://github.com/${{ github.repository }}"
      fallback-repo-url: "https://github.com/${{ github.repository }}"
      output-format: "html"
      output-file: "file_list.html"
      color-source: "random"
      color-list: "#FF0000 #00FF00 #0000FF #FFFF00 #FF00FF #00FFFF"
      color-range-start: "#000000"
      color-range-end: "#FFFFFF"
      file-categories: ""
      overwrite-file-categories: "false"
      ignore-list: ""
      overwrite-ignore-list: "false"
      max-attempts: "1000000"
      exclude-blacks-threshold: "#222222"
      exclude-dark-colors: "false"
      exclude-bright-colors: "false"
      exclude-blacks: "false"
      ensure-readable-colors: "false"
      repo-root-header: "Repo Root"
      header-text: "## File List"
      intro-text: "# Here is a list of files included in this repository:"
      dark-color-luminance-threshold: "128"
      bright-color-luminance-threshold: "200"
      chunk-size: "40"
      viewport-mobile: "768"
      viewport-tablet: "1024"
      viewport-small-desktop: "1440"
      root-margin-large-desktop: "0px 0px 400px 0px"
      root-margin-small-desktop: "0px 0px 300px 0px"
      root-margin-tablet: "0px 0px 200px 0px"
      root-margin-mobile: "0px 0px 100px 0px"
      respect-gitignore: "true"
      default-branch: "${{ github.event.repository.default_branch }}"
      link-ref: "${{ github.sha }}"
      gtm-id: "GTM-T8J6HPLF"
      output-file-stdout: "false"

   - name: Update README.md
     uses: actions/github-script@v7
     with:
      script: |
       const fs = require('fs');
            const readmePath = './README.md';
            let fileListPath = './file_list.md';
            const fileListHTMLPath = './file_list.html';

            // Determine which file to use based on which is newer
            if (fs.existsSync(fileListPath) && fs.existsSync(fileListHTMLPath)) {
         const fileListStat = fs.statSync(fileListPath);
         const fileListHTMLStat = fs.statSync(fileListHTMLPath);

         if (fileListHTMLStat.mtime > fileListStat.mtime) {
           fileListPath = fileListHTMLPath;
           console.log('Using file_list.html because it is newer than file_list.md');
         } else {
           console.log('Using file_list.md because it is newer than file_list.html');
         }
            } else if (fs.existsSync(fileListHTMLPath)) {
         fileListPath = fileListHTMLPath;
         console.log('Using file_list.html because file_list.md does not exist');
            } else if (!fs.existsSync(fileListPath)) {
         console.warn('Neither file_list.md nor file_list.html exist.  Aborting README.md update.');
         return;
            }

       try {
         // Check if README.md exists, if not create it
         if (!fs.existsSync(readmePath)) {
         console.warn('README.md not found. Creating a new README.md file.');
         fs.writeFileSync(readmePath, '# Project Title\n\n<!-- FILE_LIST_START -->\n<!-- FILE_LIST_END -->\n');
         }

         // Read the contents of README.md
         let readmeContent = fs.readFileSync(readmePath, 'utf8');

         // Read the contents of file_list.md
         const fileListContent = fs.readFileSync(fileListPath, 'utf8');

         // Define start and end markers for the file list section
         const startMarker = '<!-- FILE_LIST_START -->';
         const endMarker = '<!-- FILE_LIST_END -->';

         // Find the start and end positions of the file list section
         const startPosition = readmeContent.indexOf(startMarker);
         const endPosition = readmeContent.indexOf(endMarker);

         // Check if the markers exist in the README.md file
         if (startPosition === -1 || endPosition === -1) {
           console.warn('Start or end markers not found in README.md.  The action will add the markers with the file list to the end of the file.');
           readmeContent += `\n${startMarker}\n${fileListContent}\n${endMarker}\n`;
         } else {
           // Replace the existing file list with the new content
           readmeContent = readmeContent.substring(0, startPosition + startMarker.length) +
             '\n' + fileListContent + '\n' +
             readmeContent.substring(endPosition);
         }

         // Write the updated content back to README.md
         fs.writeFileSync(readmePath, readmeContent);
         console.log('Successfully updated README.md');
       } catch (error) {
         console.error('Failed to update README.md:', error);
       }

   - name: Commit and push changes
     uses: stefanzweifel/git-auto-commit-action@v5
     with:
      commit_message: "Update file list in README.md automatically with GitHub Action"
      file_pattern: "README.md"
      commit_user_name: "{{ github.actor }}"
      commit_user_email: "{{ github.actor }}@users.noreply.github.com"
      commit_author: "{{ github.actor }} <{{ github.actor }}@users.noreply.github.com>"
```

</details>

---

## ⚙️ Configuration

---

## ⚙️ Configuration

### 🎛️ Input Parameters

<details open>
<summary><b>🔧 Essential Inputs</b></summary>

| Parameter           | Description            | Default        | Options            |
| ------------------- | ---------------------- | -------------- | ------------------ |
| `directory`         | Root directory to scan | `.`            | Any valid path     |
| `output-format`     | File format            | `markdown`     | `markdown`, `html` |
| `output-file`       | Output filename        | `file_list.md` | Any filename       |
| `repo-url`          | Repository URL         | Auto-detected  | GitHub URL         |
| `respect-gitignore` | Honor `.gitignore`     | `false`        | `true`, `false`    |

</details>

<details>
<summary><b>🎨 Color & Styling Inputs</b></summary>

| Parameter                | Description             | Default                   |
| ------------------------ | ----------------------- | ------------------------- |
| `color-source`           | Color generation method | `random`                  |
| `color-list`             | Custom color palette    | `#FF0000 #00FF00 #0000FF` |
| `color-range-start`      | Min color for random    | `#000000`                 |
| `color-range-end`        | Max color for random    | `#FFFFFF`                 |
| `exclude-dark-colors`    | Skip dark colors        | `false`                   |
| `exclude-bright-colors`  | Skip bright colors      | `false`                   |
| `ensure-readable-colors` | Maintain contrast ratio | `false`                   |

</details>

<details>
<summary><b>📱 Responsive & Performance Inputs</b></summary>

| Parameter                | Description                | Default             |
| ------------------------ | -------------------------- | ------------------- |
| `chunk-size`             | Lines per lazy-load chunk  | `40`                |
| `viewport-mobile`        | Mobile breakpoint (px)     | `768`               |
| `viewport-tablet`        | Tablet breakpoint (px)     | `1024`              |
| `viewport-small-desktop` | Desktop breakpoint (px)    | `1440`              |
| `root-margin-mobile`     | Mobile intersection margin | `0px 0px 100px 0px` |
| `root-margin-tablet`     | Tablet intersection margin | `0px 0px 200px 0px` |

</details>

<details>
<summary><b>📂 File Organization Inputs</b></summary>

| Parameter                   | Description                | Default               |
| --------------------------- | -------------------------- | --------------------- |
| `file-categories`           | Custom ext/name pairs      | ` `                   |
| `overwrite-file-categories` | Replace default categories | `false`               |
| `ignore-list`               | Additional ignore patterns | ` `                   |
| `overwrite-ignore-list`     | Replace default ignores    | `false`               |
| `repo-root-header`          | Root folder header         | `Repo Root`           |
| `header-text`               | Main file list header      | `## File List`        |
| `intro-text`                | Intro paragraph            | `# Here is a list...` |

</details>

<details>
<summary><b>🔗 Version Control Inputs</b></summary>

| Parameter            | Description                                 | Default        |
| -------------------- | ------------------------------------------- | -------------- |
| `link-ref`           | Git ref for file links                      | Current branch |
| `default-branch`     | Fallback branch                             | `main`         |
| `gtm-id`             | Google Tag Manager container in HTML output | `GTM-T8J6HPLF` |
| `output-file-stdout` | Print to stdout                             | `false`        |
| `log-level`          | Logging verbosity                           | `INFO`         |

</details>

---

## 📖 Examples

### 🎨 HTML Output with Custom Colors

```yaml
- uses: nick2bad4u/generate-repo-file-list@v1
  with:
   output-format: "html"
   output-file: "file_list.html"
   color-source: "list"
   color-list: "#FF6B6B #4ECDC4 #45B7D1 #FFA07A #98D8C8"
   chunk-size: "50"
```

### 📝 Markdown with Gitignore Respect

```yaml
- uses: nick2bad4u/generate-repo-file-list@v1
  with:
   output-format: "markdown"
   respect-gitignore: "true"
   ignore-list: "build dist .venv"
```

### 🏷️ Custom File Categories

```yaml
- uses: nick2bad4u/generate-repo-file-list@v1
  with:
   file-categories: ".tsx TypeScript .vue Vue .rs Rust"
   overwrite-file-categories: "false"
```

---

## 🧪 Running Tests

```powershell
# Install dependencies
pip install -r requirements.txt

# Run test suite
pytest
```

```bash
# Linux/macOS
pip install -r requirements.txt && pytest
```

---

## 🔄 Versioning and Releases

This action uses **automated semantic versioning** 🤖. Every push to `main` triggers intelligent version detection:

### 📈 Version Bump Rules

| Commit Pattern            | Bump Type    | Example             |
| ------------------------- | ------------ | ------------------- |
| `BREAKING CHANGE` or `!:` | 🔴 **Major** | `v1.0.0` → `v2.0.0` |
| `feat:` or `feature:`     | 🟡 **Minor** | `v1.0.0` → `v1.1.0` |
| All others                | 🟢 **Patch** | `v1.0.0` → `v1.0.1` |

### ✅ Recommended Usage

**Option 1:** Auto-update with latest compatible version (recommended)

```yaml
- uses: nick2bad4u/generate-repo-file-list@v1
```

**Option 2:** Pin to specific version for maximum stability

```yaml
- uses: nick2bad4u/generate-repo-file-list@v1.2.3
```

### 💬 Commit Message Examples

```bash
# 🟢 Patch: v1.0.0 → v1.0.1
git commit -m "fix: correct Windows path handling"

# 🟡 Minor: v1.0.0 → v1.1.0
git commit -m "feat: add lazy loading for large repos"

# 🔴 Major: v1.0.0 → v2.0.0
git commit -m "feat!: restructure input parameters

BREAKING CHANGE: renamed 'file-list' to 'output-file'"
```

> 📚 **Learn More**: See [VERSIONING.md](VERSIONING.md) for complete release documentation.

---

## 📊 Output Examples

### 🎭 Markdown Format Preview

```markdown
## File List

### Repo Root

- [.gitignore](https://github.com/user/repo/blob/main/.gitignore)
- [README.md](https://github.com/user/repo/blob/main/README.md)
- [requirements.txt](https://github.com/user/repo/blob/main/requirements.txt)

### Python

- [src/app.py](https://github.com/user/repo/blob/main/src/app.py)
- [tests/test_app.py](https://github.com/user/repo/blob/main/tests/test_app.py)
```

### 🌈 HTML Format Preview

The HTML output includes:

- ✨ Vibrant color-coded file links
- 📱 Responsive lazy loading
- 🎯 Organized categorization
- ⚡ Performance-optimized rendering

> 🌐 **Live Demo**: Visit our [GitHub Pages](https://nick2bad4u.github.io/generate-repo-file-list/) to see HTML output in action!

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. 🍴 Fork the repository
2. 🌿 Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. ✅ Commit your changes (`git commit -m 'feat: add some amazing feature'`)
4. 📤 Push to the branch (`git push origin feature/AmazingFeature`)
5. 🎉 Open a Pull Request

---

## 📄 License

This is free and unencumbered software released into the **public domain** under [The Unlicense](LICENSE).

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.

For more information, see <https://unlicense.org>.

---

## 🙏 Acknowledgments

- Built with ❤️ using Python and GitHub Actions
- Inspired by the need for better repository documentation
- Thanks to all contributors and users!

---

<div align="center">

### ⭐ If you find this useful, please star the repository!

Made with 💙 by [Nick2bad4u](https://github.com/Nick2bad4u)

[Report Bug](https://github.com/Nick2bad4u/generate-repo-file-list/issues) • [Request Feature](https://github.com/Nick2bad4u/generate-repo-file-list/issues) • [View Releases](https://github.com/Nick2bad4u/generate-repo-file-list/releases)

</div>

---

<!-- FILE_LIST_START -->

## File List

# Here is a list of files included in this repository:

### Repo Root

- [.gitignore](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/.gitignore)
- [.jsbeautifyrc](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/.jsbeautifyrc)
- [.prettierrc](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/.prettierrc)
- [CNAME](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/CNAME)
- [CODE_OF_CONDUCT.md](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/CODE_OF_CONDUCT.md)
- [CONTRIBUTING.md](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/CONTRIBUTING.md)
- [LICENSE](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/LICENSE)
- [README.md](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/README.md)
- [VERSIONING.md](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/VERSIONING.md)
- [dockerfile](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/dockerfile)
- [file_list.html](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/file_list.html)
- [file_list.md](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/file_list.md)
- [requirements.txt](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/requirements.txt)

### JavaScript

- [.eslintrc.js](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/.eslintrc.js)

### YAML

- [.github/workflows/auto-release.yml](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/.github/workflows/auto-release.yml)
- [.github/workflows/main.yml](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/.github/workflows/main.yml)
- [action.yml](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/action.yml)

### src

- [src/**init**.py](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/src/__init__.py)
- [src/generate_file_list.py](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/src/generate_file_list.py)

### tests

- [tests/test_generate_file_list.py](https://github.com/Nick2bad4u/generate-repo-file-list/blob/main/tests/test_generate_file_list.py)

<!-- FILE_LIST_END -->

---

## 📋 Example Output

### Markdown Format

The Markdown output generates clean, standard Markdown links organized by category:

```markdown
## File List

# Here is a list of files included in this repository:

### Repo Root

- [.gitignore](https://github.com/your-org/your-repo/blob/main/.gitignore)
- [README.md](https://github.com/your-org/your-repo/blob/main/README.md)
- [package.json](https://github.com/your-org/your-repo/blob/main/package.json)

### JavaScript

- [index.js](https://github.com/your-org/your-repo/blob/main/index.js)
- [utils.js](https://github.com/your-org/your-repo/blob/main/utils.js)

### Python

- [src/main.py](https://github.com/your-org/your-repo/blob/main/src/main.py)
- [tests/test_main.py](https://github.com/your-org/your-repo/blob/main/tests/test_main.py)
```

### HTML Format

The HTML output includes vibrant colors, lazy loading for performance, and responsive design:

```html
<h1>## File List</h1>
<p># Here is a list of files included in this repository:</p>

<div
 class="lazyload-placeholder"
 data-content="file-list-1"
 style="min-height: 400px;"
></div>

<script>
 // Lazy loading script with viewport-aware configuration
 // Chunks load progressively as user scrolls
 // Colors randomly generated for visual distinction
</script>
```

**Live HTML Preview:** View the actual generated HTML with colors and lazy loading at [GitHub Pages](https://nick2bad4u.github.io/generate-repo-file-list/file_list.html)

> **Note:** GitHub's Markdown renderer doesn't display inline HTML styles. For the full colorful experience, view the HTML file directly or through GitHub Pages.
