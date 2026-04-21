from pathlib import Path


def test_prompt_templates_have_balanced_code_fences():
    prompt_dir = Path("src/devpilot/prompts")
    prompt_files = sorted(prompt_dir.glob("*.txt"))

    assert prompt_files, "No prompt templates found."

    for prompt_file in prompt_files:
        content = prompt_file.read_text(encoding="utf-8")
        fence_count = content.count("```")
        assert fence_count % 2 == 0, f"Unbalanced code fences in {prompt_file}"
