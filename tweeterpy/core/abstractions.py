import inspect
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional, Union
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from x_client_transaction import ClientTransaction

HttpMethod = Literal["GET", "POST", "PUT",
                     "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"]

RequestHook = Callable[..., Union[None, Dict[str, Any],
                                  Awaitable[Union[None, Dict[str, Any]]]]]
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
        return inspect.iscoroutinefunction(self._send)

    @property
    @abstractmethod
    def cookies(self) -> Any:
        raise NotImplementedError

    @property
    @abstractmethod
    def headers(self) -> Any:
        raise NotImplementedError

    def _run_request_hooks(self, hooks: List[RequestHook], url: str, method: HttpMethod, **kwargs: Any) -> Dict[str, Any]:
        """Runs pre-request hooks to prepare the execution context."""
        for hook in hooks:
            if inspect.iscoroutinefunction(hook):
                raise RuntimeError(
                    f"Cannot run async hook {hook.__name__} in a synchronous session.")

            result = hook(url=url, method=method, **kwargs)
            if isinstance(result, dict):
                url = result.get("url", url)
                method = result.get("method", method)
                # Filter out url/method and update the main kwargs
                kwargs.update({k: v for k, v in result.items()
                              if k not in ["url", "method"]})

        return {"url": url, "method": method, **kwargs}

    async def _run_request_hooks_async(self, hooks: List[RequestHook], url: str, method: HttpMethod, **kwargs: Any) -> Dict[str, Any]:
        for hook in hooks:
            result = hook(url=url, method=method, **kwargs)
            if inspect.isawaitable(result):
                result = await result

            if isinstance(result, dict):
                url = result.get("url", url)
                method = result.get("method", method)
                kwargs.update({k: v for k, v in result.items()
                              if k not in ["url", "method"]})

        return {"url": url, "method": method, **kwargs}

    def _run_response_hooks(self, hooks: List[ResponseHook], response: Any, **context: Any) -> Any:
        """Runs post-request hooks to transform the response object."""
        for hook in hooks:
            if inspect.iscoroutinefunction(hook):
                raise RuntimeError(
                    f"Cannot run async hook {hook.__name__} in a synchronous session.")

            # Each hook receives the current response and the context used to get it
            transformed = hook(response=response, **context)

            # If the hook returns a value, it becomes the response for the NEXT hook
            if transformed is not None:
                response = transformed
        return response

    async def _run_response_hooks_async(self, hooks: List[ResponseHook], response: Any, **context: Any) -> Any:
        for hook in hooks:
            result = hook(response=response, **context)

            if inspect.isawaitable(result):
                result = await result

            if result is not None:
                response = result
        return response

    @abstractmethod
    def _send(self, url: str, method: HttpMethod, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def update_headers(self, headers: Dict[str, str]) -> None:
        raise NotImplementedError

    def _prepare_headers(self, url: str, method: HttpMethod, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = headers if isinstance(headers, dict) else {}
        if isinstance(self.client_transaction, ClientTransaction):
            transaction_id = self.client_transaction.generate_transaction_id(
                method=method, path=urlparse(url).path)
            headers["x-client-transaction-id"] = transaction_id
        return headers

    def _process_response(self, response: Any) -> Union[BeautifulSoup, Dict[str, Any]]:
        headers = response.headers
        content_type = str(headers.get(
            "Content-Type", headers.get("content-type", ""))).lower()
        if "json" in content_type:
            return response.json()

        return BeautifulSoup(response.content, "html.parser")

    def _sync_request(self, url: str, method: HttpMethod, **kwargs) -> Union[BeautifulSoup, Dict[str, Any]]:
        context = self._run_request_hooks(
            hooks=self.request_hooks, url=url, method=method, **kwargs)

        response = self._send(**context)

        response = self._run_response_hooks(
            hooks=self.response_hooks, response=response, **context)
        return self._process_response(response=response)

    async def _async_request(self, url: str, method: HttpMethod, **kwargs) -> Union[BeautifulSoup, Dict[str, Any]]:
        context = await self._run_request_hooks_async(hooks=self.request_hooks, url=url, method=method, **kwargs)

        response = await self._send(**context)

        response = await self._run_response_hooks_async(hooks=self.response_hooks, response=response, **context)
        return self._process_response(response=response)

    def request(self, url: str, method: Optional[HttpMethod] = None, **kwargs):
        if method is None:
            method = "GET"
        headers = self._prepare_headers(
            url=url, method=method, headers=kwargs.pop("headers", {}))
        kwargs["headers"] = headers

        if self.is_async:
            return self._async_request(url=url, method=method, **kwargs)

        return self._sync_request(url=url, method=method, **kwargs)


# INTERFACES


if __name__ == "__main__":
    pass
