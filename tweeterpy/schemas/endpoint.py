from typing import Optional

from pydantic import model_validator

from tweeterpy.schemas.base import TweeterPySchema
from tweeterpy.schemas.route import Route


class Endpoint(TweeterPySchema):
    name: Optional[str] = None
    route: Route

    @model_validator(mode="after")
    def set_default_name(self):
        if self.name is None:
            self.name = self.route.operation_name
        return self

    @staticmethod
    def from_slug(slug: str, name: Optional[str] = None, **kwargs) -> "Endpoint":
        if "/" not in slug:
            raise ValueError(
                f"Invalid slug format: '{slug}'. "
                "Expected format: 'queryId/operationName'"
            )
        query_id, _, operation_name = slug.strip("/").partition("/")

        return Endpoint(name=name or operation_name, route=Route(query_id=query_id, operation_name=operation_name), **kwargs)

    @property
    def method(self) -> str:
        return self.route.operation_type.http_method

    @property
    def path(self) -> str:
        return self.route.full_path

    def __str__(self) -> str:
        return f"{self.method} {self.path}"


if __name__ == "__main__":
    pass
