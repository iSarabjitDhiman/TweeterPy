from typing import Any, Dict, List, Optional, Union

from pydantic import Field, model_serializer

from tweeterpy.schemas.base import TweeterPySchema


class ToggleMap(TweeterPySchema):
    data: Dict[str, Any] = Field(default_factory=dict)

    def all_true(self, names: List[str]) -> bool:
        return all(self.is_true(name) for name in names)

    def any_true(self, names: List[str]) -> bool:
        return any(self.is_true(name) for name in names)

    def clear(self):
        """Resets all toggles/features in this map."""
        self.data.clear()
        return self

    def disable(self, name: Union[str, List[str]]):
        """Sets one or more toggles to False."""
        names_list = [name] if isinstance(name, str) else name
        self.data.update({name: False for name in names_list if name in self.data})
        return self

    def enable(self, name: Union[str, List[str]]):
        """Sets one or more toggles to True."""
        names_list = [name] if isinstance(name, str) else name
        self.data.update({name: True for name in names_list if name in self.data})
        return self

    def get(self, name: Union[str, List[str]], default: Any = None):
        """Retrieves specific toggles from the map."""
        names_list = [name] if isinstance(name, str) else name

        if default is not None:
            return {name: self.data.get(name, default) for name in names_list}

        return {name: self.data.get(name) for name in names_list if name in self.data}

    def get_array_value(self, name: str, default: Optional[List] = None):
        if default is None:
            default = []

        value = self.get_value(name=name)
        return value if isinstance(value, list) else default

    def get_list_value(self, name: str, default: Optional[List] = None):
        self.get_array_value(name=name, default=default)

    def get_number_value(
        self, name: str, default: Union[int, float] = 0
    ) -> Union[int, float]:
        value = self.get_value(name=name)
        return value if isinstance(value, (int, float)) else default

    def get_string_value(self, name: str, default: str = "") -> str:
        value = self.get_value(name=name)
        return value if isinstance(value, str) else default

    def get_value(self, name: str, default: Any = None):
        return self.data.get(name, default)

    def has_one(self, name: str, allowed_values: List) -> bool:
        return self.get_value(name=name) in allowed_values

    def has_value(self, name: str, expected_value: Any) -> bool:
        return self.get_value(name=name) == expected_value

    def is_true(self, name: str) -> bool:
        return self.get_value(name=name) is True

    def set(self, name: str, value: Any):
        """Sets a toggle to any value (bool, int, str, list, etc.)"""
        self.data[name] = value
        return self

    def update(self, data: Dict[str, Any]):
        """Updates existing toggles."""
        for key, value in data.items():
            if (
                key in self.data
                and isinstance(self.data[key], dict)
                and isinstance(value, dict)
            ):
                self.data[key].update(value)
            else:
                self.data[key] = value
        return self

    @property
    def payload(self) -> Dict[str, Any]:
        """Returns the dictionary for the API request."""
        return self.data

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """
        Forces Pydantic to treat this model as the dictionary itself.
        This removes the 'data' key from the output.
        """
        return self.data


class FeatureSwitches(ToggleMap):
    @property
    def switches(self) -> Dict[str, Any]:
        return self.data


class FieldToggles(ToggleMap):
    @property
    def toggles(self) -> Dict[str, Any]:
        return self.data


class Metadata(TweeterPySchema):
    feature_switches: FeatureSwitches = Field(default_factory=FeatureSwitches)
    field_toggles: FieldToggles = Field(default_factory=FieldToggles)


if __name__ == "__main__":
    pass
