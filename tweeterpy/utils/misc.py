from tweeterpy.utils.casing import CasingType, transform_casing


class DotNotationMeta(type):
    def __getattr__(cls, name: str):
        normalized_name = transform_casing(name, target=CasingType.UPPER_SNAKE)
        if hasattr(cls, normalized_name):
            return getattr(cls, normalized_name)

        raise AttributeError(
            f"Type '{cls.__name__}' has no attribute '{name}'")

    def __setattr__(cls, name, value):
        normalized_name = transform_casing(name, target=CasingType.UPPER_SNAKE)
        if hasattr(cls, normalized_name):
            raise AttributeError(f"Attribute '{name}' is read-only.")

        super().__setattr__(normalized_name, value)

    def __dir__(cls):
        return sorted(set(super().__dir__()))


if __name__ == "__main__":
    pass
