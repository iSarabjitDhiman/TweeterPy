from typing import Any, Dict

from pydantic import AliasGenerator, ConfigDict
from pydantic.alias_generators import to_camel

from tweeterpy.schemas.base import TweeterPySchema


class TweeterPyVariableSchema(TweeterPySchema):
    """Intermediate base for outgoing GraphQL variable payloads."""

    model_config = ConfigDict(
        # Generates aliases for BOTH validation (incoming) and serialization (outgoing model_dump)
        use_enum_values=True,
        alias_generator=AliasGenerator(
            validation_alias=to_camel, serialization_alias=to_camel
        ),
    )

    def to_payload(self) -> Dict[str, Any]:
        """Converts model to X API payload, honoring aliases and stripping out None values."""
        return self.model_dump(by_alias=True, exclude_none=True)


if __name__ == "__main__":
    pass
