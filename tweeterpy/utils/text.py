import json
import re
from typing import Any, List, Optional

from bs4 import BeautifulSoup

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


def parse_html(data: Any, parser: Optional[str] = None) -> BeautifulSoup:
    """Parses input data into a BeautifulSoup object for DOM manipulation."""
    if isinstance(data, BeautifulSoup):
        return data

    if parser is None:
        parser = "html.parser"

    html_str = to_string(data=data)
    return BeautifulSoup(markup=html_str, features="html.parser")


def parse_json(data: Any, default: Optional[Any] = None) -> Any:
    """Safely converts string/bytes/response to a dictionary."""
    if data is None:
        return default

    if isinstance(data, dict):
        return data

    if hasattr(data, "json") and callable(data.json):
        return data.json()

    str_data = to_string(data)
    return json.loads(str_data)


if __name__ == "__main__":
    pass
