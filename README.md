[![PyPI](https://img.shields.io/pypi/v/devpilot-hq)](https://pypi.org/project/devpilot-hq/) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15670806.svg)](https://doi.org/10.5281/zenodo.15670806)


# DevPilot HQ

**CLI tool to onboard, explain, and refactor legacy codebases using local LLMs via Ollama. Supports Python, Django, React, Java, C, and C++.**

---

## What is DevPilot?

DevPilot is a command-line developer companion designed for:

* **Onboarding**: Generate a high-level, human-readable summary of the project structure and logic
* **Explaining**: Understand what a file is doing, in detail
* **Refactoring**: Get blunt, actionable suggestions to clean up old or messy code

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

* Python 3.7+
* Ollama running locally or remotely

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

* ✅ Python / Django
* ✅ React (JSX/TSX)
* ✅ Java
* ✅ C / C++

Prompt templates live in the `prompts/` folder. DevPilot dynamically selects the correct one.

---

## Prompt Templates

| Template File            | Description                   |
| ------------------------ | ----------------------------- |
| `base_prompt.txt`        | Used for project onboarding   |
| `explain_prompt.txt`     | Used to explain a single file |
| `refactor_prompt.txt`    | Suggests code improvements    |
| `*_react/java/c/etc.txt` | Language-specific variants    |

These are stored outside the Python package and bundled for binaries using PyInstaller.

---

## Output and Logs

* Output is cleaned from Markdown to readable plain text
* Logs are saved by default
* User can set custom log location

```bash
.onboarder_log.txt  # default name
~/Documents/        # default path if unspecified
```

Logs are overwritten each time.

---

## Features

* Language-aware prompts
* Automatic log saving and path resolution
* Interactive follow-up by default
* Streaming response display
* Smart prompt truncation
* Fully offline (no cloud calls)
* Works with any Ollama model

---

## Remote Ollama Support

To use DevPilot with a remote instance:

```bash
export OLLAMA_HOST=http://192.168.1.100:11434
devpilot ./myrepo --mode=onboard --model=llama3
```

---

## Roadmap

* [x] Multi-mode CLI (onboard, explain, refactor)
* [x] Prompt size handling & streaming
* [x] Interactive follow-up
* [x] Language detection & prompt routing
* [x] PyPI packaging + binary releases
* [ ] VSCode extension
* [ ] LSP & auto-complete integration
* [ ] Unit test generation

---

## File Structure

```
DevPilot-HQ/
├── .github/workflows/release.yml   # CI/CD GitHub Actions
├── bootstrap.sh                    # One-file installer
├── pyproject.toml                  # Build + metadata
├── README.md
├── prompts/
│   ├── explain_prompt.txt
│   ├── refactor_prompt.txt
│   └── ...
└── src/
    └── devpilot/
        ├── onboarder.py        # CLI entrypoint
        ├── onboard.py
        ├── explain.py
        ├── refactor.py
        ├── prompt.py
        ├── log_utils.py
        ├── interactive.py
        └── ollama_infer.py
```

---

## License

MIT — see [`LICENSE`](./LICENSE).

---

## Author

**Sandeeb Adhikari**
GitHub: [@SandeebAdhikari](https://github.com/SandeebAdhikari)

---

**Built for devs who’d rather refactor than rot.**

