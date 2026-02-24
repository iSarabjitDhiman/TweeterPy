import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, Literal, Optional, Union
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from x_client_transaction import ClientTransaction

HttpMethod = Literal["GET", "POST", "PUT",
                     "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"]

# ABSTRACT CLASSES


class TweeterPySession(ABC):
    """
    Base class for HTTP sessions.

    This abstract class defines the required contract for both Synchronous 
    and Asynchronous session implementations (e.g., curl_cffi, httpx).
    """

    def __init__(self) -> None:
        self.client_transaction: Optional[ClientTransaction] = None

    @property
    @abstractmethod
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

    @abstractmethod
    def update_headers(self, headers: Dict[str, str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def _send(self, url: str, method: HttpMethod, **kwargs) -> Any:
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
        response = self._send(method=method, url=url, **kwargs)
        return self._process_response(response=response)

    async def _async_request(self, url: str, method: HttpMethod, **kwargs) -> Union[BeautifulSoup, Dict[str, Any]]:
        response = await self._send(method=method, url=url, **kwargs)
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
