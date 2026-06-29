from __future__ import annotations

from typing import Dict, Optional

from tweeterpy.core.resources import XFeatures, XFieldToggleRules, XOperations
from tweeterpy.schemas import Metadata, Operation
from tweeterpy.schemas.metadata import FeatureSwitch, FieldToggle
from tweeterpy.schemas.types import OperationData, OperationVariables
from tweeterpy.utils.casing import Casing, CasingType
from tweeterpy.utils.misc import resolve_metadata


class APIDefinition:
    DEFAULT_CASING = CasingType.PASCAL

    def __init__(
        self,
        feature_switch: FeatureSwitch,
        field_toggle: FieldToggle,
        operations: Optional[Dict[str, OperationData]] = None,
    ):
        self._operations: Dict[str, OperationData] = {}
        self.feature_switch = feature_switch
        self.field_toggle = field_toggle
        self.operations = operations

    def _normalize_data(
        self, data: Dict[str, OperationData]
    ) -> Dict[str, OperationData]:
        """Converts all keys in a dictionary to the internal standard casing."""
        return {
            Casing.transform(text=key, case_type=self.DEFAULT_CASING): value
            for key, value in data.items()
        }

    @property
    def operations(self) -> Dict[str, OperationData]:
        return self._operations

    @operations.setter
    def operations(self, operations: Optional[Dict[str, OperationData]]):
        if not isinstance(operations, dict):
            self._operations = {}
            return

        self._operations = self._normalize_data(data=operations)

    @classmethod
    def from_defaults(
        cls, operations: Optional[Dict[str, OperationData]] = None
    ) -> APIDefinition:
        """
        Factory method to initialize APIDefinition with internal
        XFeatures and XFieldToggleRules defaults.
        """
        # 1. Initialize the base resolvers
        feature_switch = FeatureSwitch(custom_overrides=XFeatures().to_dict())
        field_toggle = FieldToggle(
            feature_switch=feature_switch,
            disabled_fields=XFieldToggleRules.DISABLED_FIELDS,
            rules_mapping=XFieldToggleRules.RULES_MAPPING,
        )

        # 2. Return a new instance of this class
        return cls(
            feature_switch=feature_switch,
            field_toggle=field_toggle,
            operations=operations,
        )

    def create_operation(
        self,
        operation_name: str,
        variables: Optional[OperationVariables] = None,
        should_resolve_metadata: bool = True,
    ) -> Operation:
        operation = self.get_operation_data(operation_name=operation_name)

        # Merge dynamic variables
        if variables:
            operation.variables.update(variables)

        # Build the final metadata (resolved switches/toggles)
        if should_resolve_metadata:
            operation.metadata = self.resolve_operation_metadata(operation)

        return operation

    def get_operation_data(self, operation_name: str) -> Operation:
        normalized_operation_name = Casing.transform(
            text=operation_name, case_type=self.DEFAULT_CASING
        )
        if normalized_operation_name in self._operations:
            operation_data = self._operations.get(normalized_operation_name)
            if operation_data:
                base_operation = Operation.from_raw_operation_data(
                    operation_data=operation_data
                )
                return base_operation.model_copy(deep=True)

        operation_template = getattr(XOperations, normalized_operation_name, None)
        if isinstance(operation_template, Operation):
            return operation_template.model_copy(deep=True)

        raise KeyError(
            f"Operation '{operation_name}' not found in live definition or XOperations presets. "
            f"Please ensure the operation name is correct or try running the APIUpdater."
        )

    def resolve_operation_metadata(self, operation: Operation) -> Metadata:
        """Resolves raw feature/toggle names into X-compliant value dictionaries."""
        operation_metadata = operation.metadata

        feature_switches = operation_metadata.feature_switches
        resolved_features = resolve_metadata(
            metadata=feature_switches, resolver_func=self.feature_switch.resolve
        )

        toggle_names = operation_metadata.field_toggles
        resolved_toggles = resolve_metadata(
            metadata=toggle_names, resolver_func=self.field_toggle.resolve
        )

        return Metadata(
            feature_switches=resolved_features, field_toggles=resolved_toggles
        )


if __name__ == "__main__":
    pass
