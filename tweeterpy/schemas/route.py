import re
from typing import Optional

from pydantic import field_validator

from tweeterpy.schemas.base import TweeterPySchema
from tweeterpy.schemas.constants import OperationType


class Route(TweeterPySchema):
    operation_name: str
    operation_type: OperationType = OperationType.QUERY
    query: Optional[str] = None
    query_id: str

    @field_validator("query_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not (15 <= len(v) <= 40):
            raise ValueError(f"Query ID '{v}' has a suspicious length ({len(v)}).")

        if not re.match(r"^[A-Za-z0-9_\-]+$", v):
            raise ValueError(f"Query ID '{v}' contains invalid characters.")

        return v

    @property
    def path(self) -> str:
        return f"{self.query_id}/{self.operation_name}"

    def __str__(self) -> str:
        return self.path


if __name__ == "__main__":
    pass
