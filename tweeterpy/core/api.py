from enum import Enum
from typing import Any, Dict, Optional

from tweeterpy.core.abstractions import ResponseType, TweeterPySession
from tweeterpy.core.graphql import GraphQLClient
from tweeterpy.schemas.operation import Operation


class APIClient:
    def __init__(
        self,
        graphql_client: GraphQLClient,
        session: TweeterPySession,
        host: str,
        timeout: Optional[int] = 9000,
        **kwargs,
    ) -> None:
        self.session = session
        self.graphql_client = graphql_client
        self.timeout = timeout
        self.host = host

    def dispatch(
        self,
        path: str,
        method: str,
        host: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        response_type: Optional[ResponseType] = None,
        **kwargs,
    ):
        if host is None:
            host = self.host
        if timeout is None:
            timeout = self.timeout
        if response_type is None:
            response_type = ResponseType.AUTO

        url = f"{host.rstrip('/')}/{path.lstrip('/')}"
        return self.session.request(
            url=url,
            method=method,
            params=params,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout,
            response_type=response_type,
            **kwargs,
        )

    def graphql(
        self,
        operation: Operation,
        variables: Dict[str, Any],
        headers: Dict[str, Any],
        timeout: Optional[int] = None,
        force_post: Optional[bool] = False,
        **kwargs,
    ):
        request_payload = self.graphql_client.prepare_request(
            operation=operation,
            variables=variables,
            headers=headers,
            timeout=timeout,
            force_post=force_post,
            **kwargs,
        )
        return self.dispatch(**request_payload)

    def graphql_full_response(self):
        return self.graphql_client.prepare_request

    def get(
        self,
        params: Dict[str, Any],
        endpoint: str,
        headers: Dict[str, Any],
        host: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"/1.1/{endpoint}{extension}",
            method="GET",
            params=params,
            headers=headers,
            host=host,
        )

    def get_i(
        self,
        params: Dict[str, Any],
        headers: Dict[str, Any],
        endpoint: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"/i/{endpoint}{extension}",
            method="GET",
            params=params,
            headers=headers,
        )

    def get_urt(
        self,
        params: Dict[str, Any],
        headers: Dict[str, Any],
        timeout: int,
        endpoint: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"/2/{endpoint}{extension}",
            method="GET",
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def get_unversioned(
        self, path: str, params: Dict[str, Any], headers: Dict[str, Any], host: str
    ):
        return self.dispatch(
            path=path, method="GET", params=params, headers=headers, host=host
        )

    def delete(
        self,
        data: Any,
        params: Dict[str, Any],
        headers: Dict[str, Any],
        endpoint: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"/1.1/{endpoint}{extension}",
            method="DELETE",
            data=data,
            params=params,
            headers=headers,
        )

    def delete_urt(
        self,
        params: Dict[str, Any],
        headers: Dict[str, Any],
        endpoint: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"/2/{endpoint}{extension}",
            method="DELETE",
            params=params,
            headers=headers,
        )

    def delete_unversioned(
        self, path: str, params: Dict[str, Any], headers: Dict[str, Any], host: str
    ):
        return self.dispatch(
            path=path, method="DELETE", params=params, headers=headers, host=host
        )

    def post(
        self,
        data: Any,
        host: str,
        params: Dict[str, Any],
        headers: Dict[str, Any],
        endpoint: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"1.1/{endpoint}{extension}",
            host=host,
            method="POST",
            data=data,
            params=params,
            headers=headers,
        )

    def post_i(
        self,
        data: Any,
        headers: Dict[str, Any],
        endpoint: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"/i/{endpoint}{extension}", method="POST", data=data, headers=headers
        )

    def post_unversioned(
        self, path: str, data: Any, headers: Dict[str, Any], host: str
    ):
        return self.dispatch(
            path=path, method="POST", data=data, headers=headers, host=host
        )

    def post_urt(
        self,
        data: Any,
        params: Dict[str, Any],
        headers: Dict[str, Any],
        endpoint: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"/2/{endpoint}{extension}",
            method="POST",
            data=data,
            params=params,
            headers=headers,
        )

    def post_form(
        self,
        data: Any,
        params: Dict[str, Any],
        headers: Dict[str, Any],
        endpoint: str,
        extension: str = ".json",
    ):
        headers = {**headers, "content-type": "multipart/form-data"}
        return self.dispatch(
            path=f"/2/{endpoint}{extension}",
            method="POST",
            data=data,
            params=params,
            headers=headers,
        )

    def put(
        self,
        data: Any,
        headers: Dict[str, Any],
        endpoint: str,
        extension: str = ".json",
    ):
        return self.dispatch(
            path=f"1.1/{endpoint}{extension}", method="PUT", data=data, headers=headers
        )

    def put_unversioned(self, path: str, data: Any, headers: Dict[str, Any], host: str):
        return self.dispatch(
            path=path, method="PUT", data=data, headers=headers, host=host
        )

    def jetfuel(self, path: str, headers: Dict[str, Any], host: str):
        return self.dispatch(
            path=path,
            method="GET",
            headers=headers,
            host=host,
            response_type=ResponseType.RAW,
        )

    def jetfuel_form(self, path: str, headers: Dict[str, Any], host: str, data: Any):
        return self.dispatch(
            path=path,
            method="POST",
            headers=headers,
            host=host,
            data=data,
            response_type=ResponseType.RAW,
        )


if __name__ == "__main__":
    pass
