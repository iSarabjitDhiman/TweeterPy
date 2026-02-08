from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from tweeterpy.schemas.base import TweeterPySchema


class ToggleMap(TweeterPySchema):
    data: Dict[str, Any] = Field(default_factory=dict)

    def clear(self):
        """Resets all toggles/features in this map."""
        self.data.clear()
        return self

    def enable(self, name: Union[str, List[str]]):
        """Sets one or more toggles to True."""
        names_list = [name] if isinstance(name, str) else name
        self.data.update(
            {name: True for name in names_list if name in self.data})
        return self

    def disable(self, name: Union[str, List[str]]):
        """Sets one or more toggles to False."""
        names_list = [name] if isinstance(name, str) else name
        self.data.update(
            {name: False for name in names_list if name in self.data})
        return self

    def get(self, name: Union[str, List[str]], default: Optional[bool] = None):
        """Retrieves specific toggles from the map."""
        names_list = [name] if isinstance(name, str) else name

        if default is not None and isinstance(default, bool):
            return {name: self.data.get(name, default) for name in names_list}

        return {name: self.data.get(name) for name in names_list if name in self.data}

    def set(self, name: str, value: Any):
        """Sets a toggle to any value (bool, int, str, list, etc.)"""
        self.data[name] = value
        return self

    @property
    def payload(self) -> Dict[str, Any]:
        """Returns the dictionary for the API request."""
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
