from enum import Enum


class OperationType(Enum):
    MUTATION = "mutation"
    QUERY = "query"

    @property
    def http_method(self) -> str:
        mapping = {OperationType.QUERY: "GET", OperationType.MUTATION: "POST"}
        return mapping.get(self)


if __name__ == "__main__":
    pass
