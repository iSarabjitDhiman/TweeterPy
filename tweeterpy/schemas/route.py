import re

from pydantic import field_validator

from tweeterpy.schemas.base import TweeterPySchema
from tweeterpy.schemas.constants import OperationType


class Route(TweeterPySchema):
    query_id: str
    operation_name: str
    operation_type: OperationType = OperationType.QUERY

    @property
    def full_path(self) -> str:
        return f"{self.query_id}/{self.operation_name}"

    @field_validator("query_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not (15 <= len(v) <= 40):
            raise ValueError(f"Query ID '{v}' has a suspicious length ({len(v)}).")

        if not re.match(r"^[A-Za-z0-9_\-]+$", v):
            raise ValueError(f"Query ID '{v}' contains invalid characters.")

        return v

    def __str__(self) -> str:
        return self.full_path


if __name__ == "__main__":
    pass
