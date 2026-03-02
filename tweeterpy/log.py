import inspect
import logging.config
import os
from typing import Any, Optional, Type, Union

from tweeterpy.constants import LOGGING_CONFIG
from tweeterpy.core.abstractions import TweeterPyLogger

logging.config.dictConfig(LOGGING_CONFIG)


class Logger:
    @staticmethod
    def get_logger(
        logger: Optional[Union[TweeterPyLogger, Type[TweeterPyLogger]]],
        name: str,
        *args,
        **kwargs,
    ):
        if isinstance(logger, TweeterPyLogger):
            return logger

        if isinstance(logger, type) and issubclass(logger, TweeterPyLogger):
            kwargs.update({"name": name})
            return logger(*args, **kwargs)

        return StandardLogger(name=name)


class StandardLogger(TweeterPyLogger):
    _CURRENT_FILE = os.path.normcase(__file__)

    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name=name)
        super().__init__()

    def _get_dynamic_stacklevel(self) -> int:
        stack = inspect.stack()
        # Start at 2 (0 is this method, 1 is the debug/info/error method)
        for depth, frame in enumerate(stack[2:], start=2):
            if os.path.normcase(frame.filename) != self._CURRENT_FILE:
                return depth
        return 2

    def set_level(self, level: Union[str, int]) -> None:
        if isinstance(level, str):
            level = level.upper()

        self.logger.setLevel(level)

        for handler in self.logger.handlers:
            handler.setLevel(level)

    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        return self.logger.debug(
            msg=message, stacklevel=self._get_dynamic_stacklevel(), *args, **kwargs
        )

    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        return self.logger.info(
            msg=message, stacklevel=self._get_dynamic_stacklevel(), *args, **kwargs
        )

    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        return self.logger.warning(
            msg=message, stacklevel=self._get_dynamic_stacklevel(), *args, **kwargs
        )

    def error(self, message: Any, *args: Any, **kwargs: Any) -> None:
        return self.logger.error(
            msg=message, stacklevel=self._get_dynamic_stacklevel(), *args, **kwargs
        )

    def exception(self, message: Any, *args: Any, **kwargs: Any) -> None:
        return self.logger.exception(
            msg=message, stacklevel=self._get_dynamic_stacklevel(), *args, **kwargs
        )


if __name__ == "__main__":
    pass
