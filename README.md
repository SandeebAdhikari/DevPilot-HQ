[![PyPI](https://img.shields.io/pypi/v/devpilot-hq)](https://pypi.org/project/devpilot-hq/)


# DevPilot HQ

**CLI tool to onboard, explain, and refactor legacy codes bases for python, c, javaand c++ using local LLMs via Ollama.**

---

## What is DevPilot?

DevPilot is a command-line developer companion designed for:

- **Onboarding**: Generate a human-readable overview of a codebase (files + logic summary)
- **Explaining**: Understand a single file's purpose (e.g., `models.py` or `views.py`)
- **Refactoring**: Get suggestions to clean up old or confusing code

It runs **100% locally** using [Ollama](https://ollama.com), and works with self-hosted models like `llama2`, `codellama`, or `mistral`.

---

## Installation

```
git clone https://github.com/SandeebAdhikari/DevPilot-HQ.git
cd DevPilot-HQ
bash bootstrap.sh
```

This sets up a virtual environment, installs DevPilot in editable mode, and adds the devpilot CLI globally.

---

## Requirements
* Python 3.7+
* Ollama running locally or remotely

**Pull a model:**
```
ollama pull llama2
```

**Start Ollama:**
```
# Option 1: Locally
ollama run llama2

# Option 2: With Docker
docker run -d -p 11434:11434 ollama/ollama
```
---

## Usage
```
# Onboard a full project
devpilot /path/to/project --mode=onboard --model=llama2

# Explain a single file
devpilot /path/to/models.py --mode=explain --model=llama2

# Suggest refactors
devpilot /path/to/views.py --mode=refactor --model=llama2
```

---

## File Structure
```
DevPilot-HQ/
├── bootstrap.sh              # One-file installer
├── setup.py                  # CLI packaging
├── README.md                 # This file
├── prompts/                  # Prompt templates (outside package)
│   ├── base_prompt.txt
│   ├── explain_prompt.txt
│   └── refactor_prompt.txt
└── devpilot/
    ├── onboarder.py          # CLI entrypoint
    ├── onboard.py            # Onboarding logic
    ├── explain.py            # File explanation
    ├── refactor.py           # Refactoring suggestions
    ├── ollama_infer.py       # Runs Ollama (local or remote)
    ├── prompt.py             # Resolves prompt paths
    ├── log_utils.py          # Prompt user for log location
    └── interactive.py        # Interactive follow-up loop
```

---

## Prompt Templates
Each mode uses a dedicated prompt template stored in devpilot/prompts/.

| Template File | Description | 
| --- | --- | 
| `base_prompt.txt` | For full repo onboarding | 
| `explain_prompt.txt` | For single file explanation | 
| `refactor_prompt.txt` | For refactoring recommendations |

---

## Output Formatting
Markdown-style output from models is converted into clean plain text in the terminal. For example:

- `## Header` → Printed as bold text with underlines
- `* Bullet` → Printed as • Bullet

A full log (prompt + output) is saved to:
```
.onboarder_log.txt
```
This file appears inside the scanned repo or next to the scanned file.

---

## Log File Control 
DevPilot now asks where you want to save your logs. 
- You can enter a custom path. 
- If left blank, logs default to your system’s `~/Documents/` folder. 
- Log is always overwritten (not appended) for clarity.”

---

## Prompt Size Handling 
To avoid model timeouts or errors: 
* If the prompt grows beyond ~2500 tokens, older parts may be truncated. 
* You’ll see a warning if the prompt gets too long. 
* Helps maintain reliability during interactive follow-up loops.


---

## Remote Ollama Support
To use a remote Ollama instance (e.g., a home server or Docker host):

```
export OLLAMA_HOST=http://192.168.1.100:11434
devpilot /path/to/project --mode=onboard --model=llama2
```
Make sure the port is exposed on your server.

---

## Philosophy
- Offline-first, privacy-focused
- No OpenAI key or cloud API required
- No telemetry or lock-in
- Secure packaging planned with PyInstaller

### Why?
$1.5B is wasted on dev onboarding every year. This tool is designed to reduce ramp-up time — especially in solo-dev and small-team environments.

---

## Roadmap

- [x] Multi-mode CLI (`onboard`, `explain`, `refactor`)
- [x] Markdown rendering → terminal-safe formatting
- [x] Remote Ollama support
- [x] Interactive follow-up by default
- [x] Prompt streaming
- [x] Prompt truncation for stability
- [ ] Generate unit tests
- [ ] PyInstaller packaging
- [ ] LSP + VSCode integration (planned)

---

##  Author
**Sandeeb Adhikari**  
[github.com/SandeebAdhikari](https://github.com/SandeebAdhikari)

---

##  License MIT

This project is licensed under the [MIT License](./LICENSE).

---

**Built for devs who’d rather refactor than rot.**

