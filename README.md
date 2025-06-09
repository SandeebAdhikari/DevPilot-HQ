# DevPilot HQ

**AI-powered CLI tool to onboard, explain, and refactor legacy Django codebases.**

---

## What is DevPilot?
DevPilot is a developer tool that uses local LLMs (via [Ollama](https://ollama.com)) to:

- **Scan and explain** unstructured legacy Django projects
- **Onboard** new developers fast with clear summaries
- **Refactor** old code with senior dev recommendations

No OpenAI keys. No bullshit. 100% local.

---

## Features

| Command                                   | Description                                      |
|------------------------------------------|--------------------------------------------------|
| `<file_path> --mode=onboard` | Full codebase tree + overview explanation        |
| `<file_path --mode=explain` | Explain a single Python file (models, views etc.)|
| `<file_path --mode=refactor`| Suggest refactors for a legacy file              |


## Installation (One-liner)

```bash
git clone https://github.com/SandeebAdhikari/DevPilot-HQ.git
cd DevPilot-HQ
bash bootstrap.sh
```

This will:
- Create a Python virtual environment
- Install DevPilot in editable mode
- Add the `devpilot` command to your environment

---

## Requirements
- Python 3.7+
- [Ollama](https://ollama.com) installed and running (e.g., `ollama run llama2`)

We recommend pulling a model before you start:

```bash
ollama pull codellama:13b
```
---

## Usage Examples

```bash
# Onboard a full repo
 devpilot /path/to/project --mode=onboard

# Explain a single file (e.g., models.py)
 devpilot /path/to/models.py --mode=explain

# Suggest refactors for views.py
 devpilot /path/to/views.py --mode=refactor
```

---

##  Prompt Templates
Located in `prompts/`:
- `base_prompt.txt` → used for full repo onboarding
- `explain_prompt.txt` → used for file explanations
- `refactor_prompt.txt` → used for smart refactor advice

---

##  File Structure

```
DevPilot_HQ/
├── bootstrap.sh              # One-file installer
├── setup.py                  # Makes DevPilot installable as a CLI tool
├── onboarder.py              # CLI entrypoint (dispatches commands)
├── commands/
│   ├── onboard.py            # Full project scan + analysis
│   ├── explain.py            # Single file explainer
│   └── refactor.py           # Single file refactorer
└── prompts/
    ├── base_prompt.txt
    ├── explain_prompt.txt
    └── refactor_prompt.txt
```

---

##  Philosophy
- 100% offline by default
- No cloud dependency
- No API keys or telemetry
- No hidden .py files (packaged via PyInstaller in future)

### Why?
$1.5B is wasted on dev onboarding every year. This tool is designed to reduce ramp-up time — especially in solo-dev and small-team environments.

---

##  Author
**Sandeeb Adhikari**  
[github.com/SandeebAdhikari](https://github.com/SandeebAdhikari)

---

##  License MIT

This project is licensed under the [MIT License](./LICENSE).

---

##  Coming Soon
- Automatic test case generation
- Patch file suggestions
- Language server support for live code feedback

---

Built for devs who’d rather refactor than rot.
 









