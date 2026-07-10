from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    Union,
    cast,
    get_args,
    overload,
)

from typing_extensions import TypeVar

from tweeterpy.core.middleware import HookDispatcher
from tweeterpy.schemas.constants import HttpMethod, ResponseType
from tweeterpy.utils.misc import is_json_response
from tweeterpy.utils.text import parse_html, parse_json, to_string

if TYPE_CHECKING:
    from x_client_transaction import ClientTransaction

    from tweeterpy.core.api import APIClient, AsyncAPIClient
    from tweeterpy.schemas.types import (
        Headers,
        HTMLResponse,
        JSONResponse,
        RequestHook,
        Response,
        ResponseHook,
    )

# ABSTRACT CLASSES


class TweeterPySession(ABC):
    """
    Base class for HTTP sessions.

    This abstract class defines the required contract for both Synchronous
    and Asynchronous session implementations (e.g., curl_cffi, httpx).
    """

    def __init__(self) -> None:
        self.client_transaction: Optional[ClientTransaction] = None
        self.hook_dispatcher: HookDispatcher = HookDispatcher(session=self)
        self.request_hooks: List[RequestHook] = []
        self.response_hooks: List[ResponseHook] = []

    @property
    @abstractmethod
    def cookies(self) -> Any:
        raise NotImplementedError

    @property
    @abstractmethod
    def headers(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def request(
        self,
        url: str,
        method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET,
        *,
        response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def update_headers(self, headers: Headers) -> None:
        raise NotImplementedError

    def _process_response(
        self, response: Response, response_type: ResponseType.ALL_LITERAL
    ) -> Any:
        if response_type == ResponseType.RAW or not response:
            return response

        if response_type == ResponseType.AUTO:
            response_type = (
                ResponseType.JSON
                if is_json_response(response=response)
                else ResponseType.TEXT
            )

        if response_type == ResponseType.JSON:
            return parse_json(data=response)

        if response_type == ResponseType.HTML:
            return parse_html(data=response)

        return to_string(data=response)

    def _validate_method(
        self, method: Union[HttpMethod.ALL_LITERAL, str]
    ) -> HttpMethod.ALL_LITERAL:
        upper_method = method.upper()
        valid_methods = get_args(HttpMethod.ALL_LITERAL)
        if upper_method not in valid_methods:
            raise ValueError(
                f"Invalid HTTP Method: '{upper_method}'. Must be one of {valid_methods}"
            )
        return cast(HttpMethod.ALL_LITERAL, upper_method)


class TweeterPySyncSession(TweeterPySession, ABC):
    @abstractmethod
    def _send(self, url: str, method: HttpMethod.ALL_LITERAL, **kwargs) -> Response:
        """The actual synchronous HTTP transport implementation."""
        raise NotImplementedError

    # fmt:off
    @overload
    def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.HTML_LITERAL, **kwargs: Any) -> HTMLResponse: ...
    @overload
    def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.JSON_LITERAL, **kwargs: Any) -> JSONResponse: ...
    @overload
    def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.TEXT_LITERAL, **kwargs: Any) -> str: ...
    @overload
    def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.ANY_LITERAL = ResponseType.AUTO, **kwargs: Any) -> Any: ...

    def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs: Any) -> Any:
    # fmt:on
        method = self._validate_method(method=method)
        initial_context = {"url": url, "method": method, **kwargs}
        request_context = self.hook_dispatcher.run_request_hooks(
            hooks=self.request_hooks, initial_context=initial_context
        )

        raw_response = self._send(**request_context)
        hooked_response = self.hook_dispatcher.run_response_hooks(
            hooks=self.response_hooks,
            response=raw_response,
            context=request_context,
        )

        return self._process_response(
            response=hooked_response, response_type=response_type
        )


class TweeterPyAsyncSession(TweeterPySession, ABC):
    @abstractmethod
    async def _send(
        self, url: str, method: HttpMethod.ALL_LITERAL, **kwargs: Any
    ) -> Response:
        """The actual asynchronous HTTP transport implementation."""
        raise NotImplementedError

    # fmt:off
    @overload
    async def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.HTML_LITERAL, **kwargs: Any) -> HTMLResponse: ...
    @overload
    async def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.JSON_LITERAL, **kwargs: Any) -> JSONResponse: ...
    @overload
    async def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.TEXT_LITERAL, **kwargs: Any) -> str: ...
    @overload
    async def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.ANY_LITERAL = ResponseType.AUTO, **kwargs: Any) -> Any: ...

    async def request(self, url: str, method: Union[HttpMethod.ALL_LITERAL, str] = HttpMethod.GET, *, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs: Any) -> Any:
    # fmt:on
        method = self._validate_method(method=method)
        initial_context = {"url": url, "method": method, **kwargs}
        request_context = await self.hook_dispatcher.run_request_hooks_async(
            hooks=self.request_hooks, initial_context=initial_context
        )

        raw_response = await self._send(**request_context)
        hooked_response = await self.hook_dispatcher.run_response_hooks_async(
            hooks=self.response_hooks,
            response=raw_response,
            context=request_context,
        )

        return self._process_response(
            response=hooked_response, response_type=response_type
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


APIClientType = TypeVar(
    "APIClientType",
    bound=Union["APIClient", "AsyncAPIClient"],
    default="APIClient",
)

SessionType = TypeVar(
    "SessionType",
    bound=Union["TweeterPySyncSession", "TweeterPyAsyncSession"],
    default="TweeterPySyncSession",
)

if __name__ == "__main__":
    pass
