from devpilot.detect_lang import infer_repo_language

def test_infer_most_common_language():
    repomap = {
        "a.py": {"language": "python"},
        "b.py": {"language": "python"},
        "c.jsx": {"language": "react"},
    }
    assert infer_repo_language(repomap) == "python"

def test_infer_language_with_tie():
    repomap = {
        "a.py": {"language": "python"},
        "b.java": {"language": "java"},
    }
    # Any of them could be valid (no tiebreaker logic), just check one of them
    result = infer_repo_language(repomap)
    assert result in {"python", "java"}

def test_infer_fallback_to_plaintext():
    assert infer_repo_language({}) == "plaintext"

