from typing import Literal

Mode = Literal["explain", "refactor"]


def get_prompt_version(mode: Mode, lang: str) -> int:
    normalized = (lang or "plaintext").strip().lower()

    if mode == "explain":
        # v6 is the generic fallback for unknown/uncommon languages
        return {
            "python": 1,
            "java": 2,
            "c": 3,
            "cpp": 4,
            "react": 5,
        }.get(normalized, 6)

    # mode == "refactor"
    # v5 is the safest generic fallback for unknown languages.
    return {
        "python": 1,
        "c": 2,
        "cpp": 2,
        "java": 3,
        "react": 4,
    }.get(normalized, 5)
