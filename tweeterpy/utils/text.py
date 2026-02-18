import re
from typing import Any, List

from tweeterpy.core.resources import RegexPatterns


def normalize_js_object(js_str: str) -> str:
    # Fixes unquoted keys like queryId: -> "queryId":
    repaired = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', js_str)
    return repaired


def tokenize_string(text: str) -> List[str]:
    if not text:
        return []
    return [word.lower() for word in RegexPatterns.WORD_BOUNDARY_REGEX.split(text) if word]


def to_string(data: Any) -> str:
    if data is None:
        return ""

    if isinstance(data, str):
        return data

    if hasattr(data, "content") and isinstance(data.content, bytes):
        return data.content.decode("utf-8", errors="ignore")

    return str(data)


if __name__ == "__main__":
    pass
