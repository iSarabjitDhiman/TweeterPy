from typing import (
    Any,
    Awaitable,
    Dict,
    List,
    Optional,
    Protocol,
    TypeAlias,
    TypedDict,
    Union,
    runtime_checkable,
)

from bs4 import BeautifulSoup
from typing_extensions import NotRequired, Required, TypeVar

from tweeterpy.schemas.constants import HttpMethod

JSONDict: TypeAlias = Dict[str, Any]
Headers: TypeAlias = Dict[str, str]
Params: TypeAlias = Dict[str, Any]
OperationVariables: TypeAlias = JSONDict
MetadataInput: TypeAlias = Union[List[str], JSONDict, None]

Response: TypeAlias = Any  # The raw response from the transport (httpx/curl_cffi)
JSONResponse: TypeAlias = Union[JSONDict, List[Any], Any]
HTMLResponse: TypeAlias = BeautifulSoup
TextResponse: TypeAlias = str

ClientResponse = TypeVar(
    "ClientResponse",
    bound=Union["HTMLResponse", "JSONResponse", "TextResponse", "Response"],
    default="Response",
)


class MetadataDict(TypedDict, total=False):
    """The internal structure of the 'metadata' key in a GraphQL operation."""

    featureSwitches: MetadataInput
    fieldToggles: MetadataInput


class OperationData(TypedDict):
    """
    The 'Blueprint' for a Twitter GraphQL operation.
    This matches the raw JSON found in Twitter's main.js or external API configs.
    """

    queryId: NotRequired[str]
    operationName: str
    operationType: str
    metadata: MetadataDict
    variables: NotRequired[OperationVariables]
    query: NotRequired[str]


class RequestContext(TypedDict, total=False):
    """
    The standardized envelope for every Twitter request.
    Using total=False allows the dictionary to be 'open' to extra keys
    like 'proxy' or 'impersonate' while still validating required fields.
    """

    url: Required[str]
    method: Required[HttpMethod.ALL_LITERAL]
    headers: NotRequired[Headers]
    params: NotRequired[Params]
    json: NotRequired[JSONDict]
    data: NotRequired[Any]
    timeout: NotRequired[int]
    session: NotRequired[Any]


@runtime_checkable
class RequestHook(Protocol):
    """
    Protocol for pre-request hooks.
    Can return a dict to update context or None.
    """

    def __call__(
        self, context: RequestContext
    ) -> Union[Optional[RequestContext], Awaitable[RequestContext]]: ...


@runtime_checkable
class ResponseHook(Protocol):
    """
    Protocol for post-request hooks.
    Receives the response and the context used to generate it.
    """

    def __call__(
        self, response: Response, context: RequestContext
    ) -> Union[Optional[Response], Awaitable[Optional[Response]]]: ...


if __name__ == "__main__":
    pass
