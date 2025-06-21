from devpilot.prompt import load_prompt_template, get_prompt_path

def test_prompt_rendering_with_code():
    code_sample = "def add(a, b): return a + b"
    prompt_path = get_prompt_path("explain")

    # Call updated load_prompt_template with explicit placeholders
    rendered = load_prompt_template(
        prompt_path,
        code=code_sample,               
        lang="python",                 
        repomap_summary=code_sample     
    )

    # Ensure no unreplaced placeholders remain
    assert "{{" not in rendered

    # Ensure content was injected correctly
    assert "def add" in rendered
