from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, cast, overload

from tweeterpy.core.abstractions import (
    SessionType,
    TweeterPyAsyncSession,
    TweeterPySyncSession,
)
from tweeterpy.core.graphql import GraphQLClient
from tweeterpy.schemas.constants import APIVersion, ResponseType
from tweeterpy.schemas.types import (
    ClientResponse,
    Headers,
    HttpMethod,
    JSONDict,
    OperationVariables,
    Params,
)

if TYPE_CHECKING:
    from x_client_transaction import ClientTransaction

    from tweeterpy.schemas.operation import Operation
    from tweeterpy.schemas.types import HTMLResponse, JSONResponse


class BaseAPIClient(Generic[SessionType]):
    def __init__(
        self,
        graphql_client: GraphQLClient,
        session: SessionType,
        host: str,
        timeout: Optional[int] = 9000,
        **kwargs,
    ) -> None:
        self._session = session
        self.graphql_client = graphql_client
        self.timeout = timeout
        self.host = host

    @property
    def session(self) -> SessionType:
        """Access the underlying sync/async session transport layer directly."""
        return self._session

    @property
    def client_transaction(self) -> Optional[ClientTransaction]:
        """Get the ClientTransaction instance."""
        return getattr(self.session, "client_transaction", None)

    @client_transaction.setter
    def client_transaction(self, instance: ClientTransaction) -> None:
        """Assign or safely refresh the ClientTransaction engine on the session."""
        if hasattr(self.session, "client_transaction"):
            self.session.client_transaction = instance

    @property
    def cookies(self) -> Any:
        """Access the current cookies cookie-jar from the underlying session transport layer."""
        return self.session.cookies

    @property
    def headers(self) -> Headers:
        """Access the headers configured on the session."""
        return self.session.headers

    def _prepare_payload(
        self,
        endpoint: str,
        method: str,
        version: APIVersion,
        extension: str = ".json",
        **kwargs,
    ) -> Dict[str, Any]:
        request_endpoint = endpoint.lstrip("/")

        path = (
            f"/{request_endpoint}"
            if version is APIVersion.UNVERSIONED
            else f"/{version.value}/{request_endpoint}{extension}"
        )

        return {"path": path, "method": method.upper(), **kwargs}

    @abstractmethod
    def dispatch(self, *args: Any, **kwargs: Any) -> Any:
        """Core dispatch driver. Must be implemented by concrete client subclasses."""
        raise NotImplementedError("Subclasses must implement the dispatch engine.")


class APIClient(BaseAPIClient[TweeterPySyncSession]):
    """Synchronous X Endpoints Orchestrator Client."""

    # fmt:off
    def __init__(self, graphql_client: GraphQLClient, session: TweeterPySyncSession, host: str, timeout: Optional[int] = 9000, **kwargs) -> None:
        super().__init__(graphql_client=graphql_client, session=session, host=host, timeout=timeout, **kwargs)

    @overload
    def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = ..., params: Optional[Params] = ..., data: Optional[Any] = ..., json: Optional[JSONDict] = ..., headers: Optional[Headers] = ..., timeout: Optional[int] = ..., *, response_type: ResponseType.HTML_LITERAL, **kwargs: Any) -> HTMLResponse: ...
    @overload
    def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = ..., params: Optional[Params] = ..., data: Optional[Any] = ..., json: Optional[JSONDict] = ..., headers: Optional[Headers] = ..., timeout: Optional[int] = ..., *, response_type: ResponseType.JSON_LITERAL, **kwargs: Any) -> JSONResponse: ...
    @overload
    def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = ..., params: Optional[Params] = ..., data: Optional[Any] = ..., json: Optional[JSONDict] = ..., headers: Optional[Headers] = ..., timeout: Optional[int] = ..., *, response_type: ResponseType.TEXT_LITERAL, **kwargs: Any) -> str: ...
    @overload
    def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = ..., params: Optional[Params] = ..., data: Optional[Any] = ..., json: Optional[JSONDict] = ..., headers: Optional[Headers] = ..., timeout: Optional[int] = ..., *, response_type: ResponseType.ANY_LITERAL = ResponseType.AUTO, **kwargs: Any) -> Any: ...

    def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = None, params: Optional[Params] = None, data: Optional[Any] = None, json: Optional[JSONDict] = None, headers: Optional[Headers] = None, timeout: Optional[int] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs: Any) -> Any:
        if host is None:
            host = self.host
        if timeout is None:
            timeout = self.timeout

        url = path if path.startswith(("http://", "https://")) else f"{host.rstrip('/')}/{path.lstrip('/')}"
        url = kwargs.pop("url", url)

        request_kwargs = {"params": params, "data": data, "json": json, "headers": headers, "timeout": timeout, **kwargs}
        return self.session.request(url=url, method=method, response_type=response_type, **request_kwargs)

    @overload
    def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = ..., *, response_type: ResponseType.HTML_LITERAL, **kwargs: Any) -> HTMLResponse: ...
    @overload
    def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = ..., *, response_type: ResponseType.JSON_LITERAL, **kwargs: Any) -> JSONResponse: ...
    @overload
    def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = ..., *, response_type: ResponseType.TEXT_LITERAL, **kwargs: Any) -> str: ...
    @overload
    def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = ..., *, response_type: ResponseType.ANY_LITERAL = ResponseType.RAW, **kwargs: Any) -> Any: ...

    def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.RAW, **kwargs):
        return self.dispatch(path=path, method=method, host=host, response_type=response_type, **kwargs)

    def graphql(self, operation: Operation, variables: OperationVariables, headers: Optional[Headers] = None, timeout: Optional[int] = None, force_post: Optional[bool] = False, **kwargs: Any):
        request_payload = self.graphql_client.prepare_request(operation=operation, variables=variables, headers=headers, timeout=timeout, force_post=force_post)
        return self.dispatch(**request_payload, **kwargs)

    def get(self, endpoint: str, version: APIVersion = APIVersion.V1, params: Optional[Params] = None, headers: Optional[Headers] = None, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs) -> ClientResponse:
        request_payload = self._prepare_payload(endpoint=endpoint, version=version, method=HttpMethod.GET, params=params, headers=headers, host=host, **kwargs)
        return cast(ClientResponse, self.dispatch(**request_payload, response_type=response_type))

    def post(self, endpoint: str, version: APIVersion = APIVersion.V1, data: Optional[Any] = None, json: Optional[JSONDict] = None, params: Optional[Params] = None, headers: Optional[Headers] = None, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs) -> ClientResponse:
        request_payload = self._prepare_payload(endpoint=endpoint, version=version, method=HttpMethod.POST, data=data, json=json, params=params, headers=headers, host=host, **kwargs)
        return cast(ClientResponse, self.dispatch(**request_payload, response_type=response_type))

    def put(self, endpoint: str, version: APIVersion = APIVersion.V1, data: Optional[Any] = None, json: Optional[JSONDict] = None, params: Optional[Params] = None, headers: Optional[Headers] = None, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs) -> ClientResponse:
        request_payload = self._prepare_payload(endpoint=endpoint, version=version, method=HttpMethod.PUT, data=data, json=json, params=params, headers=headers, host=host, **kwargs)
        return cast(ClientResponse, self.dispatch(**request_payload, response_type=response_type))

    def delete(self, endpoint: str, version: APIVersion = APIVersion.V1, params: Optional[Params] = None, headers: Optional[Headers] = None, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs) -> ClientResponse:
        request_payload = self._prepare_payload(endpoint=endpoint, version=version, method=HttpMethod.DELETE, params=params, headers=headers, host=host, **kwargs)
        return cast(ClientResponse, self.dispatch(**request_payload, response_type=response_type))

    def post_form(self, endpoint: str, data: Any, version: APIVersion = APIVersion.V2, params: Optional[Params] = None, headers: Optional[Headers] = None, **kwargs):
        if headers is None:
            headers = {}
        headers.update({"content-type": "multipart/form-data"})
        return self.post(endpoint=endpoint, version=version, data=data, params=params, headers=headers, **kwargs)
    # fmt:on


class AsyncAPIClient(BaseAPIClient[TweeterPyAsyncSession]):
    """Asynchronous X Endpoints Orchestrator Client."""

    # fmt:off
    def __init__(self, graphql_client: GraphQLClient, session: TweeterPyAsyncSession, host: str, timeout: Optional[int] = 9000, **kwargs
    ) -> None:
        super().__init__(graphql_client=graphql_client, session=session, host=host, timeout=timeout, **kwargs)

    @overload
    async def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = ..., params: Optional[Params] = ..., data: Optional[Any] = ..., json: Optional[JSONDict] = ..., headers: Optional[Headers] = ..., timeout: Optional[int] = ..., *, response_type: ResponseType.HTML_LITERAL, **kwargs: Any) -> HTMLResponse: ...
    @overload
    async def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = ..., params: Optional[Params] = ..., data: Optional[Any] = ..., json: Optional[JSONDict] = ..., headers: Optional[Headers] = ..., timeout: Optional[int] = ..., *, response_type: ResponseType.JSON_LITERAL, **kwargs: Any) -> JSONResponse: ...
    @overload
    async def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = ..., params: Optional[Params] = ..., data: Optional[Any] = ..., json: Optional[JSONDict] = ..., headers: Optional[Headers] = ..., timeout: Optional[int] = ..., *, response_type: ResponseType.TEXT_LITERAL, **kwargs: Any) -> str: ...
    @overload
    async def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = ..., params: Optional[Params] = ..., data: Optional[Any] = ..., json: Optional[JSONDict] = ..., headers: Optional[Headers] = ..., timeout: Optional[int] = ..., *, response_type: ResponseType.ANY_LITERAL = ResponseType.AUTO, **kwargs: Any) -> Any: ...

    async def dispatch(self, path: str, method: HttpMethod.ALL_LITERAL, host: Optional[str] = None, params: Optional[Params] = None, data: Optional[Any] = None, json: Optional[JSONDict] = None, headers: Optional[Headers] = None, timeout: Optional[int] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs: Any) -> Any:
        if host is None:
            host = self.host
        if timeout is None:
            timeout = self.timeout
            
        url = path if path.startswith(("http://", "https://")) else f"{host.rstrip('/')}/{path.lstrip('/')}"
        url = kwargs.pop("url", url)

        request_kwargs = {"params": params, "data": data, "json": json, "headers": headers, "timeout": timeout, **kwargs}
        return await self.session.request(url=url, method=method, response_type=response_type, **request_kwargs)

    @overload
    async def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = ..., *, response_type: ResponseType.HTML_LITERAL, **kwargs: Any) -> HTMLResponse: ...
    @overload
    async def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = ..., *, response_type: ResponseType.JSON_LITERAL, **kwargs: Any) -> JSONResponse: ...
    @overload
    async def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = ..., *, response_type: ResponseType.TEXT_LITERAL, **kwargs: Any) -> str: ...
    @overload
    async def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = ..., *, response_type: ResponseType.ANY_LITERAL = ResponseType.RAW, **kwargs: Any) -> Any: ...

    async def request(self, path: str, method: HttpMethod.ALL_LITERAL = HttpMethod.GET, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.RAW, **kwargs):
        return await self.dispatch(path=path, method=method, host=host, response_type=response_type, **kwargs)

    async def graphql(self, operation: Operation, variables: OperationVariables, headers: Optional[Headers] = None, timeout: Optional[int] = None, force_post: Optional[bool] = False, **kwargs: Any):
        request_payload = self.graphql_client.prepare_request(operation=operation, variables=variables, headers=headers, timeout=timeout, force_post=force_post)
        return await self.dispatch(**request_payload, **kwargs)

    async def get(self, endpoint: str, version: APIVersion = APIVersion.V1, params: Optional[Params] = None, headers: Optional[Headers] = None, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs) -> ClientResponse:
        request_payload = self._prepare_payload(endpoint=endpoint, version=version, method=HttpMethod.GET, params=params, headers=headers, host=host, **kwargs)
        return cast(ClientResponse, await self.dispatch(**request_payload, response_type=response_type))

    async def post(self, endpoint: str, version: APIVersion = APIVersion.V1, data: Optional[Any] = None, json: Optional[JSONDict] = None, params: Optional[Params] = None, headers: Optional[Headers] = None, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs) -> ClientResponse:
        request_payload = self._prepare_payload(endpoint=endpoint, version=version, method=HttpMethod.POST, data=data, json=json, params=params, headers=headers, host=host, **kwargs)
        return cast(ClientResponse, await self.dispatch(**request_payload, response_type=response_type))

    async def put(self, endpoint: str, version: APIVersion = APIVersion.V1, data: Optional[Any] = None, json: Optional[JSONDict] = None, params: Optional[Params] = None, headers: Optional[Headers] = None, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs) -> ClientResponse:
        request_payload = self._prepare_payload(endpoint=endpoint, version=version, method=HttpMethod.PUT, data=data, json=json, params=params, headers=headers, host=host, **kwargs)
        return cast(ClientResponse, await self.dispatch(**request_payload, response_type=response_type))

    async def delete(self, endpoint: str, version: APIVersion = APIVersion.V1, params: Optional[Params] = None, headers: Optional[Headers] = None, host: Optional[str] = None, response_type: ResponseType.ALL_LITERAL = ResponseType.AUTO, **kwargs) -> ClientResponse:
        request_payload = self._prepare_payload(endpoint=endpoint, version=version, method=HttpMethod.DELETE, params=params, headers=headers, host=host, **kwargs)
        return cast(ClientResponse, await self.dispatch(**request_payload, response_type=response_type))

    async def post_form(self, endpoint: str, data: Any, version: APIVersion = APIVersion.V2, params: Optional[Params] = None, headers: Optional[Headers] = None, **kwargs):
        if headers is None:
            headers = {}
        headers.update({"content-type": "multipart/form-data"})
        return await self.post(endpoint=endpoint, version=version, data=data, params=params, headers=headers, **kwargs)
    # fmt:on


if __name__ == "__main__":
    pass
