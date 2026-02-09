from typing import Any, Dict, Optional

from pydantic import Field

from tweeterpy.constants import FEATURE_SWITCHES_PRESET
from tweeterpy.core.resources import CasingType, transform_casing, XOperations
from tweeterpy.schemas import Endpoint, FeatureSwitches, FieldToggles, Metadata, Operation, Route
from tweeterpy.schemas.constants import OperationType


class APIDefinition:
    features: FeatureSwitches = Field(default_factory=FeatureSwitches)
    features_preset: FeatureSwitches = Field(
        default_factory=lambda: FeatureSwitches(data=FEATURE_SWITCHES_PRESET.copy()))
    operations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    def get_operation_data(self, operation_name: str) -> Dict[str, Any]:
        if operation_name in self.operations:
            return self.operations.get(transform_casing(text=operation_name, target=CasingType.UPPER_SNAKE), {})

        operation_template = getattr(XOperations, operation_name, None)
        if isinstance(operation_template, Operation):
            return operation_template.model_dump()

        raise KeyError(
            f"Operation '{operation_name}' not found in live definition or XOperations presets. "
            f"Please ensure the operation name is correct or try running the APIUpdater."
        )

    def get_features(self, operation_name: str) -> Dict[str, Any]:
        operation_data = self.get_operation_data(operation_name=operation_name)
        metadata = operation_data.get("metadata", {})
        raw_features = metadata.get(
            "featureSwitches") or metadata.get("feature_switches", [])

        if raw_features:
            if isinstance(raw_features, list):
                return {feature: self.features.get(name=feature) for feature in raw_features}

            if isinstance(raw_features, dict):
                return raw_features

        return self.features_preset.switches

    def get_toggles(self, operation_name: str) -> Dict[str, Any]:
        operation_data = self.get_operation_data(operation_name=operation_name)
        metadata = operation_data.get("metadata", {})
        fields = metadata.get("fieldToggles") or metadata.get(
            "field_toggles", [])

        if fields and isinstance(fields, list):
            return {field: True for field in fields}

        return fields if isinstance(fields, dict) else {}

    def build_metadata(self, operation_name: str) -> Metadata:
        return Metadata(
            feature_switches=FeatureSwitches(
                data=self.get_features(operation_name=operation_name)),
            field_toggles=FieldToggles(
                data=self.get_toggles(operation_name=operation_name))
        )

    def create_operation(self, operation_name: str, operation_type: Optional[OperationType] = None, query_id: Optional[str] = None, variables: Optional[Dict[str, Any]] = None) -> Operation:
        operation_data = self.get_operation_data(operation_name)

        query_id = query_id or operation_data.get(
            "query_id") or operation_data.get("queryId")
        operation_type = operation_type or operation_data.get(
            "operation_type") or operation_data.get("operationType")

        if not query_id:
            raise ValueError(
                f"Missing 'queryId' for operation '{operation_name}'. "
                f"The local definition might be corrupted or outdated. Please run APIUpdater."
            )

        if not operation_type:
            operation_type = OperationType.QUERY
            # raise ValueError(
            #     f"Missing 'operationType' for operation '{operation_name}'. "
            #     f"Ensure the operation is correctly defined in XOperations or the API definition file."
            # )

        variables = {
            **operation_data.get("variables", {}), **(variables or {})}

        endpoint = Endpoint(name=operation_name, route=Route(
            query_id=query_id, operation_name=operation_name, operation_type=operation_type))

        return Operation(
            endpoint=endpoint,
            variables=variables,
            metadata=self.build_metadata(operation_name=operation_name)
        )


if __name__ == "__main__":
    pass
