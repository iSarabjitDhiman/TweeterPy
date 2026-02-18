from enum import Enum

from tweeterpy.utils.decorators import process_casing


class CasingType(Enum):
    SNAKE = "snake_case"
    PASCAL = "PascalCase"
    CAMEL = "camelCase"
    LOWERCASE = "lowercase"
    KEBAB = "kebab-case"
    SCREAMING_SNAKE = "SCREAMING_SNAKE_CASE"
    UPPERCASE = "UPPERCASE"
    UNKNOWN = "unknown"
    TITLE_CASE = "Title Case"


class Casing:

    @staticmethod
    def identify(text: str) -> CasingType:
        if not text:
            return CasingType.UNKNOWN

        if text.islower():
            if "_" in text:
                return CasingType.SNAKE
            if "-" in text:
                return CasingType.KEBAB
            return CasingType.LOWERCASE

        if text.isupper():
            if "_" in text:
                return CasingType.SCREAMING_SNAKE
            return CasingType.UPPERCASE

        if text[0].islower():
            if any(character.isupper() and character not in ["_", "-"] for character in text):
                return CasingType.CAMEL

        if text[0].isupper():
            if any(character.islower() and character not in ["_", "-"] for character in text):
                return CasingType.PASCAL
            if text.istitle() and any(character.isspace() for character in text):
                return CasingType.TITLE_CASE

        return CasingType.UNKNOWN

    @staticmethod
    @process_casing("text")
    def normalize(text: str) -> str:
        return "".join(text)

    @staticmethod
    @process_casing("text")
    def to_camel(text: str) -> str:
        if not text:
            return ""
        return text[0] + "".join(word.capitalize() for word in text[1:])

    @staticmethod
    @process_casing("text")
    def to_kebab(text: str) -> str:
        return "-".join(text)

    @staticmethod
    @process_casing("text")
    def to_pascal(text: str) -> str:
        return "".join(word.capitalize() for word in text)

    @staticmethod
    @process_casing("text")
    def to_screaming_snake(text: str) -> str:
        return "_".join(text).upper()

    @staticmethod
    @process_casing("text")
    def to_snake(text: str) -> str:
        return "_".join(text)

    @staticmethod
    @process_casing("text")
    def to_title(text: str) -> str:
        return " ".join(word.capitalize() for word in text)

    @staticmethod
    @process_casing("text")
    def to_upper(text: str) -> str:
        return "".join(text).upper()

    @staticmethod
    def transform(text: str, case_type: CasingType) -> str:
        if not text:
            return ""

        transformers = {
            CasingType.SNAKE: Casing.to_snake,
            CasingType.KEBAB: Casing.to_kebab,
            CasingType.CAMEL: Casing.to_camel,
            CasingType.PASCAL: Casing.to_pascal,
            CasingType.SCREAMING_SNAKE: Casing.to_screaming_snake,
            CasingType.TITLE_CASE: Casing.to_title,
            CasingType.LOWERCASE: Casing.normalize,
            CasingType.UPPERCASE: Casing.to_upper,
        }
        transformer = transformers.get(case_type)
        return transformer(text) if transformer else text


if __name__ == "__main__":
    pass
