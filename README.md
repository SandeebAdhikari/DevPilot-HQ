[![PyPI](https://img.shields.io/pypi/v/devpilot-hq)](https://pypi.org/project/devpilot-hq/) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15670806.svg)](https://doi.org/10.5281/zenodo.15670806)

# DevPilot HQ

**CLI tool to onboard, explain, and refactor legacy codebases using local LLMs via Ollama. Supports Python, Django, React, Java, C, and C++.**

---

## What is DevPilot?

DevPilot is a command-line developer companion designed for:

- **Onboarding**: Generate a high-level, human-readable summary of the project structure and logic
- **Explaining**: Understand what a file is doing, in detail
- **Refactoring**: Get blunt, actionable suggestions to clean up old or messy code

It runs **100% locally** using [Ollama](https://ollama.com), working with self-hosted models like `llama3`, `codellama`, and `mistral`. No cloud, no API keys, and full control over logs and outputs.

---

## Installation

```bash
pip install devpilot-hq
```

Or from source:

```bash
git clone https://github.com/SandeebAdhikari/DevPilot-HQ.git
cd DevPilot-HQ
bash bootstrap.sh
```

This installs DevPilot in editable mode and makes the `devpilot` command globally available.

---

## Requirements

- Python 3.7+
- Ollama running locally or remotely

**Pull a model:**

```bash
ollama pull llama3
```

**Start Ollama:**

```bash
# Option 1: Locally
ollama run llama3

# Option 2: With Docker
docker run -d -p 11434:11434 ollama/ollama
```

---

## Usage

```bash
# Onboard a full project
devpilot /path/to/project --mode=onboard --model=llama3

# Explain a single file
devpilot /path/to/views.py --mode=explain --model=llama3

# Suggest refactors
devpilot /path/to/app.jsx --mode=refactor --model=llama3
```

Use `--lang` to override language detection (e.g., `--lang=java`).

---

## Language Support

DevPilot detects language from file type and uses a mode-specific prompt. Currently supported:

- ✅ Python / Django
- ✅ React (JSX/TSX)
- ✅ Java
- ✅ C / C++

Prompt templates live in the `prompts/` folder. DevPilot dynamically selects the correct one.

---

## Prompt Templates

| Template File         | Description                   |
| --------------------- | ----------------------------- |
| **`onboard_v1.txt`**  | Used for project onboarding   |
| **`explain_v1.txt`**  | Used to explain a single file |
| **`refactor_v1.txt`** | Suggests code improvements    |
| **`scaffold_v1.txt`** | Language-specific variants    |

These are stored outside the Python package and bundled for binaries using PyInstaller.

---

## Features

- Language-aware prompts
- Automatic log saving and path resolution
- Interactive follow-up by default
- Streaming response display
- Smart prompt truncation
- Fully offline (no cloud calls)
- Works with any Ollama model

---

## Remote Ollama Support

To use DevPilot with a remote instance:

```bash
export OLLAMA_HOST=http://192.168.1.100:11434
devpilot ./myrepo --mode=onboard --model=llama3
```

---

## Output, Logs, and Mapping

- **`repomap.json`**: tracks meaningful source files and skips noise (like `__init__.py`, `settings`, `migrations`, `node_modules`, `git`).

- **`repomap_cache.json`**: stores file hashes to detect changes and avoid re-processing unchanged files.

- **`relmap.json`**: adds class, function, import, and call relationships. This will support future features like inter-file tracing.

- **`README_AI.md`**: generated scaffold of project logic.

- **`README_SUMMARY.md`**: LLM-generated English summary of structure.

- **`Logs`**: Markdown logs saved under .devpilot/logs/ if and only if scaffold or summary is created. Replays are possible.

> DevPilot doesn’t save raw LLM responses unless they’re actually used.

---

## What’s New in 1.0.2

### Smarter File Mapping, Less Noise

DevPilot now intelligently walks your codebase to exclude unnecessary boilerplate like **`__init__.py`**, **`migrations/`**, **`settings.py`**, **`venv/`**, **`node_modules/`**, **`.next/`**, **`.vscode`**, **`git/`**, **`package-lock.json/`**, **`yarn.lock`**, **`pnpm-lock.yaml.lock`** .etc and test scaffolding. This ensures that **`repomap.json`** only contains meaningful logic files — not noise. The result is a drastically improved onboarding experience and prompt clarity.

This mapping runs automatically during **onboarding**, but can also be triggered manually via:

```
devpilot --generate-map
```

This generates two files:

- **`.devpilot/repomap.json`** — the high-level file summary
- **`.devpilot/repomap_cache.json`** — contains file hashes for tracking changes

```
devpilot --clean
```

You can also use **`--clean`** to fully wipe these files when needed, which is useful for stale or corrupted maps.

We are planning to release **`--refresh-map`** to detect live saved file edits, additions, or deletions without needing a full re-scan.

---

### Clean Separation of Maps and Metadata

All mapping output stays inside **`.devpilot/,`** keeping your project clean. These files drive all **DevPilot** modes but are not committed or required to run outside your environment.

---

### Auto-Generated Technical Docs for Onboarded Codebases

You can now run:

```
devpilot --relmap
```

This does three things:

Creates **`.devpilot/relmap.json`** — a rich relationship map that extracts symbol-level insights from Python files: class names, function names, function calls, and imports

Saves a human-readable scaffold to **`.devpilot/README_AI.md`**

Generates a plain-English summary using LLMs to **`.devpilot/README_SUMMARY.md`**

This functionality builds upon your **`repomap.json`**, which contains a curated list of logic-relevant files and their metadata. Now, with **`relmap.json`**, you get an extra layer of introspection — connecting structural files to the behaviors and entities inside them.

- **`repomap.json`** = file-level coverage
- **`relmap.json`** = symbol-level coverage (classes, functions, calls, imports)

This separation of structure vs. relationships forms the foundation for future features like:

- **`--trace-origin`**: trace where a class/function originated

- **`--explain-connections`**: visualize file-to-file logic relationships

- **`--scaffold-docs`**: auto-generate Markdown diagrams or flow breakdowns

Together, these maps provide the most powerful way to analyze a legacy codebase offline, without needing to run or test it.

---

### Powerful Logging System

You can now manage logs using:

```
devpilot --list-logs  <session_id>      # Show all saved sessions
devpilot --restore-log  <session_id>    # Restore and view a previous session
devpilot --cleanup-logs <days>          # Delete all saved logs by days
```

---

### Extra Flags for Power Users

| Flag                    | Description                                                                      |
| ----------------------- | -------------------------------------------------------------------------------- |
| **`--preview-prompt`**  | Shows the final prompt that would be sent to the LLM, but does not run inference |
| **`--scaffold-docs`**   | Generates only the Markdown scaffold from **`relmap.json`** (no LLM used)        |
| **`--lang=<language>`** | Overrides language detection (e.g., **`--lang=java`**)                           |

DevPilot logs every major mode (onboarding, explain, refactor, relmap) into versioned Markdown files. This is essential for audits, traceability, or keeping a changelog of what the LLM said — and why.

---

### What Are You Really Sending to the Model? (--preview-prompt)

DevPilot lets you preview the exact prompt sent to the LLM before any token is generated. This is essential for:

- Understanding why the model responds the way it does
- Debugging prompt-related hallucinations
- Auditing language and code passed to offline/enterprise models
- Building your own prompt templates

#### How Prompts Are Generated

Each prompt is built from a template file stored in the **`prompts/`** folder. These templates contain clear placeholders:

**`{{code}}`** → Replaced with the contents of a file (for explain, refactor)

**`{{repo_summary}}`** → Replaced with a smart summary of the codebase (for onboard)

**`{{lang}}`** → Used to select or tag the language of the content (python, java, etc.)

Templates are selected based on the **`--mode`** flags. For example:

- **`prompt/explain_v1.txt`** for file explanations
- **`prompt/refactor_v1.txt`** for file refactor
- **`prompt/onboard_v1.txt`** for onboarding walkthroughs

You can customize or override these templates for internal teams, different languages, or LLMs with specific formatting preferences.

#### Example Usage

Preview an explanation prompt for a file uses **`{{code}}`** and **`{{lang}}`** as input:

```
devpilot ./src/file.py --mode=explain --preview-prompt
```

Preview onboarding prompt (which uses the full **`.devpilot/repomap.json`** and **`.devpilot/relmap.json`** to get **`{{repo_summary}}`**):

```
devpilot <repo_path> --mode=onboard --preview-prompt
```

Preview refactor prompt for a Java file

```
devpilot MyApp.java --mode=refactor --preview-prompt
```

> This does not call the LLM — it only prints the prompt.

---

## Roadmap

### Phase 1: Build & Validate

- [x] Multi-mode CLI: --mode=onboard, --mode=explain, --mode=refactor
- [x] Language-aware prompt routing: Detects language or uses --lang override
- [x] Prompt size trimming & streaming output
- [x] Automatic interactive follow-up loop
- [x] Ollama model compatibility (local or remote)
- [x] Session logging system with replay/restore
- [x] Prompt templates with placeholder injection
- [x] PyPI packaging + binary-compatible bootstrapping
- [x] Smart file discovery (repomap)
- [x] Symbol-level relationship mapping (relmap)
- [x] Markdown scaffolding and summary generation
- [x] Prompt previewing without LLM calls
- [x] Standalone flags: --generate-map, --clean, --relmap, --scaffold-docs
- [x] Logging flags: --list-logs, --restore-log, --cleanup-logs

### Phase 2: Launch & Promote

- [ ] `--refresh-map` to update repomap based on recent edits
- [ ] Add README changelog generator from `logs/`
- [ ] Add global config + `.devpilotrc` file
- [ ] Launch `.deb` / `.exe` / `.pkg` binaries
- [ ] CLI flag to disable log saving (`--no-log`)
- [ ] Website with installation + CLI playground
- [ ] LLM prompt linting: detect weak prompts before LLM call

### Phase 3: Monetize & Scale

- [ ] VSCode wrapper (optional GUI)
- [ ] LSP + autocomplete overlay for explanations
- [ ] API mode with local token auth
- [ ] Team license model and config sync
- [ ] Project-specific onboarding with profiles
- [ ] Usage analytics (opt-in, local-first)

---

## File Structure

```
DevPilot-HQ/
├── .github/workflows/release.yml   # CI/CD GitHub Actions
├── bootstrap.sh                    # One-file installer
├── pyproject.toml                  # Build + metadata
├── README.md
├── prompts/
│   ├── explain_v1.txt
│   ├── refactor_v1.txt
│   └── ...
└── src/
    └── devpilot/
        ├── onboarder.py        # CLI entrypoint
        ├── onboard.py
        ├── explain.py
        ├── refactor.py
        ├── prompt.py
        ├── detect_lang.py
        ├── log_utils.py
        ├── constants.py
        ├── prompt_helpers.py
        ├── interactive.py
        ├── ollama_infer.py
        ├── repomap_utils.py        # Smart file selection for onboarding
        ├── repomap_generator.py    # Map + cache writer (triggered by --generate-map)
        ├── rel_map.py              # Symbol-based relational mapping
        └── session_logger.py       # All .md logs go through this
```

---

## License

MIT — see [`LICENSE`](./LICENSE).

---

## Author

**Sandeeb Adhikari**
GitHub: [@SandeebAdhikari](https://github.com/SandeebAdhikari)

---

> **Built for devs who’d rather refactor than rot.**
