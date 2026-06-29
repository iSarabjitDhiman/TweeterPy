from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field, computed_field, model_validator

from tweeterpy.schemas.base import TweeterPySchema
from tweeterpy.schemas.constants import OperationType
from tweeterpy.schemas.endpoint import Endpoint
from tweeterpy.schemas.metadata import Metadata
from tweeterpy.schemas.types import OperationData


class Operation(TweeterPySchema):
    endpoint: Endpoint
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Metadata = Field(default_factory=Metadata)

    @staticmethod
    def from_raw_operation_data(operation_data: OperationData) -> Operation:
        """
        Factory method to create an Operation from raw dictionary data.
        Bypasses Pylance's unpacking ambiguity by using Pydantic's internal validation.
        """
        return Operation.model_validate(operation_data)

    @model_validator(mode="before")
    @classmethod
    def normalize_raw_data(cls, data: Any) -> Any:
        """Handles the 'repacking' of flat JSON/Dict into the Route/Endpoint hierarchy."""
        if isinstance(data, dict) and ("queryId" in data or "query_id" in data):
            query = data.get("query")
            query_id = data.get("queryId") or data.get("query_id")
            operation_name = (
                data.get("operationName") or data.get("operation_name") or "Unknown"
            )
            operation_type = (
                data.get("operationType")
                or data.get("operation_type")
                or OperationType.QUERY
            )

            # Repack into Endpoint/Route structure
            data["endpoint"] = {
                "name": operation_name,
                "route": {
                    "query_id": query_id,
                    "operation_name": operation_name,
                    "operation_type": operation_type,
                    "query": query,
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
    def query(self) -> Optional[str]:
        return self.endpoint.route.query

    @computed_field
    @property
    def query_id(self) -> str:
        return self.endpoint.route.query_id

    @property
    def payload(self) -> Dict[str, Any]:
        payload = {}
        if self.variables:
            payload["variables"] = self.variables

        if self.metadata.feature_switches:
            payload["features"] = self.metadata.feature_switches

        if self.metadata.field_toggles:
            payload["fieldToggles"] = self.metadata.field_toggles
        return payload

    def __str__(self) -> str:
        return f"Operation({self.operation_name}, ID: {self.query_id} Method: {self.method})"


if __name__ == "__main__":
    pass
