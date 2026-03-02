import inspect
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Union,
    cast,
    get_args,
)

from x_client_transaction import ClientTransaction

from tweeterpy.utils.misc import is_json_response
from tweeterpy.utils.text import parse_html, parse_json, to_string


class ResponseType(Enum):
    AUTO = "auto"
    HTML = "html"
    JSON = "json"
    RAW = "raw"
    TEXT = "text"


HttpMethod = Literal[
    "GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"
]

RequestHook = Callable[
    ..., Union[None, Dict[str, Any], Awaitable[Union[None, Dict[str, Any]]]]
]
ResponseHook = Callable[..., Union[Any, Awaitable[Any]]]


# ABSTRACT CLASSES


class TweeterPySession(ABC):
    """
    Base class for HTTP sessions.

    This abstract class defines the required contract for both Synchronous
    and Asynchronous session implementations (e.g., curl_cffi, httpx).
    """

    def __init__(self) -> None:
        self.request_hooks: List[RequestHook] = []
        self.response_hooks: List[ResponseHook] = []
        self.client_transaction: Optional[ClientTransaction] = None

    @property
    def is_async(self) -> bool:
        """Determines if the session is asynchronous."""
        return inspect.iscoroutinefunction(self._send)

    @property
    @abstractmethod
    def cookies(self) -> Any:
        raise NotImplementedError

    @property
    @abstractmethod
    def headers(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def update_headers(self, headers: Dict[str, str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def _send(self, url: str, method: HttpMethod, **kwargs) -> Any:
        """The actual HTTP transport implementation."""
        raise NotImplementedError

    def _process_response(self, response: Any, response_type: ResponseType) -> Any:
        if inspect.iscoroutine(response):
            raise TypeError(
                "_process_response received a coroutine. Await the request call."
            )

        if response_type is ResponseType.RAW or not response:
            return response

        if response_type is ResponseType.AUTO:
            response_type = (
                ResponseType.JSON
                if is_json_response(response=response)
                else ResponseType.TEXT
            )

        if response_type is ResponseType.JSON:
            return parse_json(data=response)

        if response_type is ResponseType.HTML:
            return parse_html(data=response)

        return to_string(data=response)

    def _run_request_hooks(
        self, hooks: List[RequestHook], url: str, method: HttpMethod, **kwargs: Any
    ) -> Dict[str, Any]:
        """Runs pre-request hooks to prepare the execution context."""
        context = {"url": url, "method": method, "session": self, **kwargs}

        for hook in hooks:
            if inspect.iscoroutinefunction(hook):
                raise RuntimeError(
                    f"Cannot run async hook {hook.__name__} in a synchronous session."
                )

            result = hook(**context)
            if isinstance(result, dict):
                context.update(result)

        context.pop("session", None)
        return context

    async def _run_request_hooks_async(
        self, hooks: List[RequestHook], url: str, method: HttpMethod, **kwargs: Any
    ) -> Dict[str, Any]:
        context = {"url": url, "method": method, "session": self, **kwargs}

        for hook in hooks:
            result = hook(**context)
            if inspect.isawaitable(result):
                result = await result

            if isinstance(result, dict):
                context.update(result)

        context.pop("session", None)
        return context

    def _run_response_hooks(
        self, hooks: List[ResponseHook], response: Any, **context: Any
    ) -> Any:
        """Runs post-request hooks to transform the response object."""
        for hook in hooks:
            if inspect.iscoroutinefunction(hook):
                raise RuntimeError(
                    f"Cannot run async hook {hook.__name__} in a synchronous session."
                )

            # Each hook receives the current response and the context used to get it
            transformed = hook(response=response, **context)

            # If the hook returns a value, it becomes the response for the NEXT hook
            if transformed is not None:
                response = transformed
        return response

    async def _run_response_hooks_async(
        self, hooks: List[ResponseHook], response: Any, **context: Any
    ) -> Any:
        for hook in hooks:
            result = hook(response=response, **context)

            if inspect.isawaitable(result):
                result = await result

            if result is not None:
                response = result
        return response

    def _sync_request(
        self, url: str, method: HttpMethod, response_type: ResponseType, **kwargs
    ):
        context = self._run_request_hooks(
            hooks=self.request_hooks, url=url, method=method, session=self, **kwargs
        )

        response = self._send(**context)
        response = self._run_response_hooks(
            hooks=self.response_hooks, response=response, session=self, **context
        )
        return self._process_response(response=response, response_type=response_type)

    async def _async_request(
        self, url: str, method: HttpMethod, response_type: ResponseType, **kwargs
    ) -> Any:
        context = await self._run_request_hooks_async(
            hooks=self.request_hooks, url=url, method=method, session=self, **kwargs
        )

        response = await self._send(**context)
        response = await self._run_response_hooks_async(
            hooks=self.response_hooks, response=response, session=self, **context
        )
        return self._process_response(response=response, response_type=response_type)

    def _validate_method(self, method: Union[HttpMethod, str]) -> HttpMethod:
        upper_method = method.upper()
        valid_methods = get_args(HttpMethod)
        if upper_method not in valid_methods:
            raise ValueError(
                f"Invalid HTTP Method: '{upper_method}'. Must be one of {valid_methods}"
            )
        return cast(HttpMethod, upper_method)

    def request(
        self,
        url: str,
        method: Union[HttpMethod, str] = "GET",
        response_type: ResponseType = ResponseType.AUTO,
        **kwargs,
    ):
        """Automated routing based on session type."""
        method = self._validate_method(method=method)
        if self.is_async:
            return self._async_request(
                url=url, method=method, response_type=response_type, **kwargs
            )
        return self._sync_request(
            url=url, method=method, response_type=response_type, **kwargs
        )

    async def request_async(
        self,
        url: str,
        method: Union[HttpMethod, str] = "GET",
        response_type: ResponseType = ResponseType.AUTO,
        **kwargs,
    ):
        """Strictly asynchronous request."""
        if not self.is_async:
            raise RuntimeError(
                "Called .request_async() on a Sync Session. Use .request_sync() instead."
            )
        return self._async_request(
            url=url,
            method=self._validate_method(method=method),
            response_type=response_type,
            **kwargs,
        )

    def request_sync(
        self,
        url: str,
        method: Union[HttpMethod, str] = "GET",
        response_type: ResponseType = ResponseType.AUTO,
        **kwargs,
    ):
        """Strictly synchronous request."""
        if self.is_async:
            raise RuntimeError(
                "Called .request_sync() on an AsyncSession. Use await .request_async() instead."
            )
        return self._sync_request(
            url=url,
            method=self._validate_method(method=method),
            response_type=response_type,
            **kwargs,
        )

    def request_html(self, url: str, method: Union[HttpMethod, str] = "GET", **kwargs):
        return self.request(
            url=url, method=method, response_type=ResponseType.HTML, **kwargs
        )


# INTERFACES


class TweeterPyLogger(ABC):
    """
    Interface for TweeterPy loggers.
    Subclasses must implement all abstract methods.
    """

    @abstractmethod
    def set_level(self, level: Union[str, int]) -> None:
        """Change the logging level dynamically."""
        raise NotImplementedError

    @abstractmethod
    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def error(self, message: Any, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def exception(self, message: Any, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError


if __name__ == "__main__":
    pass
