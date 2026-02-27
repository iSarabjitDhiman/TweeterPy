from enum import Enum


class OperationType(Enum):
    QUERY = "query"
    MUTATION = "mutation"

    @property
    def http_method(self) -> str:
        mapping = {OperationType.QUERY: "GET", OperationType.MUTATION: "POST"}
        return mapping.get(self, "GET")


if __name__ == "__main__":
    pass
