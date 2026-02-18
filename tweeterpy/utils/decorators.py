import inspect
from functools import wraps
from typing import Callable, Any


from tweeterpy.utils.text import tokenize_string, to_string


def argument_transform(arg_name: str, transform_func: Callable[[Any], Any]):
    """Generic factory to transform a specific argument."""
    def decorator(func: Callable):
        func_signature = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound_args = func_signature.bind(*args, **kwargs)
            bound_args.apply_defaults()

            if arg_name in bound_args.arguments:
                bound_args.arguments[arg_name] = transform_func(
                    bound_args.arguments[arg_name])

            return func(*bound_args.args, **bound_args.kwargs)
        return wrapper
    return decorator


def ensure_str(arg_name: str = "text"):
    """Ensures the argument is a string (handles bytes/None)."""
    return argument_transform(arg_name, to_string)


def process_casing(arg_name: str = "text"):
    """Automatically converts a string into a List[str] of words."""
    return argument_transform(arg_name, tokenize_string)


if __name__ == "__main__":
    pass
