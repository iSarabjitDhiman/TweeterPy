from typing import Any, Dict, List, Optional, Union

from pydantic import Field, PrivateAttr

from tweeterpy.schemas.base import TweeterPySchema


class ToggleMap(TweeterPySchema):
    def all_true(self, names: List[str]) -> bool:
        return all(self.is_true(name) for name in names)

    def any_true(self, names: List[str]) -> bool:
        return any(self.is_true(name) for name in names)

    def get_array_value(self, name: str, default: Optional[List] = None):
        if default is None:
            default = []

        value = self.get_value(name=name)
        return value if isinstance(value, list) else default

    def get_list_value(self, name: str, default: Optional[List] = None):
        return self.get_array_value(name=name, default=default)

    def get_number_value(
        self, name: str, default: Union[int, float] = 0
    ) -> Union[int, float]:
        value = self.get_value(name=name)
        return value if isinstance(value, (int, float)) else default

    def get_string_value(self, name: str, default: str = "") -> str:
        value = self.get_value(name=name)
        return value if isinstance(value, str) else default

    def get_value(self, name: str, default: Any = None):
        raise NotImplementedError

    def has_one(self, name: str, allowed_values: List) -> bool:
        return self.get_value(name=name) in allowed_values

    def has_value(self, name: str, expected_value: Any) -> bool:
        return self.get_value(name=name) == expected_value

    def is_true(self, name: str) -> bool:
        return self.get_value(name=name) is True

    def resolve(
        self, names: Union[str, List[str]], default: Any = None
    ) -> Dict[str, Any]:
        """Converts a list of names into the X-compliant dict."""
        if isinstance(names, str):
            names = [names]

        return {name: self.get_value(name=name, default=default) for name in names}


class FeatureSwitchUser(TweeterPySchema):
    config: Dict[str, Any] = Field(default_factory=dict)
    impression_pointers: Dict[str, Any] = Field(default_factory=dict)
    impressions: Dict[str, Any] = Field(default_factory=dict)
    keysRead: Dict[str, Any] = Field(default_factory=dict)
    settings_version: Optional[str] = None


class FeatureSwitch(ToggleMap):
    custom_overrides: Dict[str, Any] = Field(default_factory=dict)
    debug: Dict[str, Any] = Field(default_factory=dict)
    default_config: Dict[str, Any] = Field(default_factory=dict)
    featureSetToken: Optional[str] = None
    isLoaded: bool = False
    isLoading: bool = False
    user: FeatureSwitchUser = Field(default_factory=FeatureSwitchUser)

    def disable(self, name: Union[str, List[str]]):
        """Sets one or more features to False in custom_overrides."""
        names_list = [name] if isinstance(name, str) else name

        for feature_name in names_list:
            self.set(name=feature_name, value=False)

        return self

    def enable(self, name: Union[str, List[str]]):
        """Sets one or more features to True in custom_overrides."""
        names_list = [name] if isinstance(name, str) else name

        for feature_name in names_list:
            self.set(name=feature_name, value=True)

        return self

    def get_feature_switch(self, name: str, shouldScribeImpression: bool = True):
        if shouldScribeImpression:
            # TODO: pending
            pass

        if name in self.custom_overrides:
            return {"value": self.custom_overrides.get(name)}

        user_value = self.user.config.get(name)
        if user_value is not None:
            return user_value

        default_value = self.default_config.get(name)
        if default_value is not None:
            return default_value

    def get_value(self, name: str, default: Any = None):
        feature_switch = self.get_feature_switch(name=name)
        return (
            feature_switch.get("value", default)
            if isinstance(feature_switch, dict)
            else default
        )

    def get_value_without_scribe_impression(
        self, name: str, default: Optional[Any] = None
    ):
        feature_switch = self.get_feature_switch(
            name=name, shouldScribeImpression=False
        )
        return (
            feature_switch.get("value", default)
            if isinstance(feature_switch, dict)
            else default
        )

    def set(self, name: str, value: Any):
        self.custom_overrides[name] = value
        return self

    def set_override(self, name: str, value: Any):
        return self.set(name=name, value=value)


class FieldToggle(ToggleMap):
    _session: Dict[str, Any] = PrivateAttr()
    _feature_switch: FeatureSwitch = PrivateAttr()

    DISABLED_FIELDS: List[str] = Field(default_factory=list)
    RULES_MAPPING: Dict[str, str] = Field(default_factory=dict)

    def __init__(
        self,
        feature_switch: Optional[FeatureSwitch] = None,
        session: Optional[Dict[str, Any]] = None,
        disabled_fields: Optional[List[str]] = None,
        rules_mapping: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        if disabled_fields:
            kwargs["DISABLED_FIELDS"] = disabled_fields
        if rules_mapping:
            kwargs["RULES_MAPPING"] = rules_mapping

        super().__init__(**kwargs)

        self._feature_switch = feature_switch or FeatureSwitch()
        self._session = session or {}

    def get_value(self, name: str, default: Any = None):
        return self._resolve(name=name, default=default)

    def _resolve(self, name: str, default: Any = None) -> bool:
        # Hardcoded Disables
        if name in self.DISABLED_FIELDS:
            return False

        # Session-based Logic
        if name == "isDelegate":
            return bool(self._session.get("actAsUserId", default))

        if name == "withPayments":
            is_enrolled = bool(self._session.get("xpaymentsEnrolled", default))
            can_access = bool(self._session.get("canAccessPayments", default))
            return is_enrolled and can_access

        # Feature Switch Mapping
        switch_name = self.RULES_MAPPING.get(name)
        if switch_name:
            return self._feature_switch.is_true(name=switch_name)

        return default


class Metadata(TweeterPySchema):
    feature_switches: Union[List[str], Dict[str, Any]] = Field(default_factory=list)
    field_toggles: Union[List[str], Dict[str, Any]] = Field(default_factory=list)


if __name__ == "__main__":
    pass
