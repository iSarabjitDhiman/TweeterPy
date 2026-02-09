import re
from enum import Enum


class CasingType(Enum):
    SNAKE = "snake"
    PASCAL = "pascal"
    CAMEL = "camel"
    UPPER_SNAKE = "upper_snake"


def transform_casing(text: str, target: CasingType = CasingType.SNAKE) -> str:
    if not text:
        return ""

    if isinstance(target, str):
        target = CasingType(target)

    s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    s2 = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', s1)
    s3 = re.sub(r'[^a-zA-Z0-9]+', ' ', s2)

    words = s3.lower().split()

    if not words:
        return ""

    if target is CasingType.SNAKE:
        return "_".join(words)

    if target is CasingType.PASCAL:
        return "".join(w.capitalize() for w in words)

    if target is CasingType.CAMEL:
        return words[0] + "".join(w.capitalize() for w in words[1:])

    if target is CasingType.UPPER_SNAKE:
        return "_".join(words).upper()

    # raise ValueError(f"Unsupported target casing: {target}")
    return "_".join(words)


if __name__ == "__main__":
    pass
