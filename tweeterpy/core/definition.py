from typing import Any, Dict, Optional

from tweeterpy.core.resources import XFeatures, XOperations, XUrls
from tweeterpy.schemas import Endpoint, FeatureSwitches, FieldToggles, Metadata, Operation, Route
from tweeterpy.schemas.constants import OperationType
from tweeterpy.utils.casing import Casing, CasingType


class APIDefinition:
    DEFAULT_CASING = CasingType.PASCAL

    def __init__(self, operations: Optional[Dict[str, Any]] = None, features: Optional[FeatureSwitches] = None):
        self._operations: Dict[str, Any] = {}
        self.operations = operations
        self.features_preset = FeatureSwitches(data=XFeatures().to_dict())
        self.features = features if isinstance(features, FeatureSwitches) else FeatureSwitches(
            data=features) if features else FeatureSwitches()

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converts all keys in a dictionary to the internal standard casing."""
        return {Casing.transform(text=key, case_type=self.DEFAULT_CASING): value for key, value in data.items()}

    @property
    def operations(self) -> Dict[str, Any]:
        return self._operations

    @operations.setter
    def operations(self, operations: Optional[Dict[str, Any]]):
        if not isinstance(operations, dict):
            self._operations = {}
            return

        self._operations = self._normalize_data(data=operations)

    def build_metadata(self, operation_name: str) -> Metadata:
        return Metadata(
            feature_switches=FeatureSwitches(
                data=self.get_features(operation_name=operation_name)),
            field_toggles=FieldToggles(
                data=self.get_toggles(operation_name=operation_name))
        )

    def create_operation(self, operation_name: str, operation_type: Optional[OperationType] = None, query_id: Optional[str] = None, variables: Optional[Dict[str, Any]] = None) -> Operation:
        operation_data = self.get_operation_data(operation_name=operation_name)

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

        full_url = f"{XUrls.GRAPHQL_BASE}/{query_id}/{operation_name}"

        endpoint = Endpoint(name=operation_name, route=Route(
            query_id=query_id, operation_name=operation_name, operation_type=operation_type), url=full_url)

        return Operation(
            endpoint=endpoint,
            variables=variables,
            metadata=self.build_metadata(operation_name=operation_name)
        )

    def get_features(self, operation_name: str, default: Optional[bool] = None) -> Dict[str, Any]:
        operation_data = self.get_operation_data(operation_name=operation_name)
        metadata = operation_data.get("metadata", {})
        raw_features = metadata.get(
            "featureSwitches") or metadata.get("feature_switches", [])

        if raw_features:
            if isinstance(raw_features, list):
                return self.features.get(name=raw_features, default=default)

            if isinstance(raw_features, dict):
                return raw_features

        return self.features_preset.switches

    def get_operation_data(self, operation_name: str) -> Dict[str, Any]:
        normalized_operation_name = Casing.transform(
            text=operation_name, case_type=self.DEFAULT_CASING)
        if normalized_operation_name in self.operations:
            return self.operations.get(normalized_operation_name, {})

        operation_template = getattr(
            XOperations, normalized_operation_name, None)
        if isinstance(operation_template, Operation):
            return operation_template.model_dump()

        raise KeyError(
            f"Operation '{operation_name}' not found in live definition or XOperations presets. "
            f"Please ensure the operation name is correct or try running the APIUpdater."
        )

    def get_toggles(self, operation_name: str) -> Dict[str, Any]:
        operation_data = self.get_operation_data(operation_name=operation_name)
        metadata = operation_data.get("metadata", {})
        fields = metadata.get("fieldToggles") or metadata.get(
            "field_toggles", [])

        if fields and isinstance(fields, list):
            return {field: True for field in fields}

        return fields if isinstance(fields, dict) else {}

    def update(self, operations: Optional[Dict[str, Any]] = None, features: Optional[Dict[str, Any]] = None):
        """Updates existing definitions for top-level keys (features, operations)."""
        if isinstance(operations, dict):
            self._operations.update(self._normalize_data(data=operations))

        if isinstance(features, dict):
            self.features.update(data=features)

        return self


if __name__ == "__main__":
    pass
