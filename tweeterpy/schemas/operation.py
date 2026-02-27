from typing import Any, Dict, Optional

from pydantic import Field, computed_field, model_validator

from tweeterpy.schemas.base import TweeterPySchema
from tweeterpy.schemas.constants import OperationType
from tweeterpy.schemas.endpoint import Endpoint
from tweeterpy.schemas.metadata import Metadata


class Operation(TweeterPySchema):
    endpoint: Endpoint
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Metadata = Field(default_factory=Metadata)

    @model_validator(mode="before")
    @classmethod
    def normalize_raw_data(cls, data: Any) -> Any:
        if isinstance(data, dict) and "queryId" in data:
            query_id = data.get("queryId")
            operation_name = data.get("operationName", "Unknown")
            operation_type = data.get("operationType", OperationType.QUERY)

            # Repack into Endpoint/Route structure
            data["endpoint"] = {
                "name": operation_name,
                "route": {
                    "query_id": query_id,
                    "operation_name": operation_name,
                    "operation_type": operation_type,
                },
            }
        return data

    @property
    def method(self) -> str:
        return self.endpoint.route.operation_type.http_method

    @property
    def name(self) -> str:
        return self.operation_name

    @computed_field
    @property
    def operation_name(self) -> str:
        return self.endpoint.route.operation_name

    @computed_field
    @property
    def operation_type(self) -> OperationType:
        return self.endpoint.route.operation_type

    @computed_field
    @property
    def path(self) -> str:
        return self.endpoint.path

    @computed_field
    @property
    def query_id(self) -> str:
        return self.endpoint.route.query_id

    @property
    def type(self) -> OperationType:
        return self.operation_type

    @computed_field
    @property
    def url(self) -> Optional[str]:
        return self.endpoint.url

    @property
    def payload(self) -> Dict[str, Any]:
        payload = {}
        if self.variables:
            payload["variables"] = self.variables

        if self.metadata.feature_switches.payload:
            payload["features"] = self.metadata.feature_switches.payload

        if self.metadata.field_toggles.payload:
            payload["fieldToggles"] = self.metadata.field_toggles.payload
        return payload

    def __str__(self) -> str:
        return f"Operation({self.operation_name}, ID: {self.query_id} Method: {self.method})"


if __name__ == "__main__":
    pass
