from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class TweeterPySchema(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_by_name=True, validate_by_alias=True, validate_assignment=True,
                              validate_default=True, alias_generator=AliasGenerator(validation_alias=to_camel), str_strip_whitespace=True, from_attributes=True)


if __name__ == "__main__":
    pass
