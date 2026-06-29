from enum import Enum
from typing import Literal


class HttpMethod:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    TRACE = "TRACE"

    ALL_LITERAL = Literal[
        "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE"
    ]


class ResponseType:
    AUTO = "AUTO"
    HTML = "HTML"
    JSON = "JSON"
    RAW = "RAW"
    TEXT = "TEXT"

    ANY_LITERAL = Literal["AUTO", "RAW"]
    AUTO_LITERAL = Literal["AUTO"]
    HTML_LITERAL = Literal["HTML"]
    JSON_LITERAL = Literal["JSON"]
    RAW_LITERAL = Literal["RAW"]
    TEXT_LITERAL = Literal["TEXT"]

    ALL_LITERAL = Literal["AUTO", "HTML", "JSON", "RAW", "TEXT"]


class APIVersion(Enum):
    INTERNAL = "i"
    UNVERSIONED = ""
    V1 = "1.1"
    V2 = "2"


class OperationType(Enum):
    MUTATION = "mutation"
    QUERY = "query"

    @property
    def http_method(self) -> str:
        return "POST" if self is OperationType.MUTATION else "GET"


if __name__ == "__main__":
    pass
