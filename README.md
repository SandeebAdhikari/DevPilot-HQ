# DevPilot HQ

>  The local-first CLI tool to **instantly understand unfamiliar codebases** — perfect for onboarding, handoffs, and solo exploration.

---

##  What It Does

DevPilot HQ scans a project directory and uses a local LLM (via [Ollama](https://ollama.com)) to generate a human-readable summary:

-  What the codebase does  
-  Where to start reading  
-  Key files or entry points  
-  How to run it locally

Built for **developers who don't want to depend on ChatGPT or SaaS tools**.

---

## Quick Start

### 1. Install requirements

- Python 3.9+
- [Ollama](https://ollama.com) installed and running
- A model pulled (we recommend `codellama:13b` or `llama2`)

```bash
ollama pull codellama:13b
```

### 2. Clone this repo
````
git clone https://github.com/yourusername/devpilot-hq.git
cd devpilot-hq
````

### 3. Run the CLI
```
python3 onboarder.py /path/to/repo --model llama2
```

#### Example Output


> Onboarding Summary: 
> - This is a Django utility for running admin commands.
> - The main entry point is manage.py, which loads settings and calls Django’s command-line tools.
> - To run it locally:
>   - Install dependencies
>   - Use `python manage.py runserver`


You also get a .onboarder_log.txt file with the full prompt + model output.

## CLI Options
| Option       | Description                             |
| ------------ | --------------------------------------- |
| `repo_path`  | Path to the repo you want to analyze    |
| `--model`    | Ollama model to use (default: `llama2`) |
| `--depth`    | *(Planned)* Max tree depth to display   |
| `--markdown` | *(Planned)* Output in Markdown format   |


- Philosophy
    - 100% offline by default

    - No cloud dependency

    - No API keys or telemetry

    - No hidden .py files (packaged via PyInstaller in future)

## Coming Soon
- VSCode extension

- Markdown summary export

- Language-aware model selection

- .onboarderrc config file support

### Why?
$1.5B is wasted on dev onboarding every year. This tool is designed to reduce ramp-up time — especially in solo-dev and small-team environments.

### Feedback Welcome
Try it on your repo and DM @yourtwitter or open an issue.

 License MIT
---
This project is licensed under the [MIT License](./LICENSE).








