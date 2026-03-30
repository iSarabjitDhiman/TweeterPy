import json
from typing import Any, Dict, List, Optional, Union

from tweeterpy.schemas.metadata import FeatureSwitch, FieldToggle
from tweeterpy.schemas.operation import Operation
from tweeterpy.utils.misc import resolve_metadata


class GraphQLClient:
    def __init__(
        self, feature_switch: FeatureSwitch, field_toggle: FieldToggle
    ) -> None:
        self.feature_switch = feature_switch
        self.field_toggle = field_toggle

    def get_feature_switches(
        self, metadata_features: Union[List[str], Dict[str, Any], None]
    ) -> Optional[Dict[str, Any]]:
        return resolve_metadata(
            metadata=metadata_features,
            resolver_func=lambda name: (
                self.feature_switch.get_value_without_scribe_impression(name=name)
                is True
            ),
        )

    def get_field_toggles(
        self, metadata_toggles: Union[List[str], Dict[str, Any], None]
    ) -> Optional[Dict[str, Any]]:
        return resolve_metadata(
            metadata=metadata_toggles, resolver_func=self.field_toggle.resolve
        )

    def get_graphql_path(
        self, query_id: Optional[str] = None, operation_name: Optional[str] = None
    ) -> str:
        if query_id:
            if operation_name:
                return f"/graphql/{query_id}/{operation_name}"
            return f"/graphql/{query_id}"

        return "/graphql"

    def prepare_get_request(
        self,
        variables: Dict[str, Any],
        features: Optional[Dict[str, Any]] = None,
        field_toggles: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        params = {"variables": json.dumps(variables, separators=(",", ":"))}

        if features:
            params["features"] = json.dumps(features, separators=(",", ":"))
        if field_toggles:
            params["fieldToggles"] = json.dumps(field_toggles, separators=(",", ":"))

        return {"params": params}

    def prepare_post_request(
        self,
        variables: Dict[str, Any],
        features: Optional[Dict[str, Any]] = None,
        field_toggles: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
        query_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"variables": variables}

        if query_id:
            payload["queryId"] = query_id
        elif query:
            payload["query"] = query

        if features:
            payload["features"] = features
        if field_toggles:
            payload["fieldToggles"] = field_toggles

        return {"json": payload}

    def prepare_request(
        self,
        operation: Operation,
        variables: Dict[str, Any],
        headers: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        force_post: Optional[bool] = False,
    ):
        if headers is None:
            headers = {}

        query_id = operation.query_id
        operation_name = operation.operation_name
        operation_type = operation.operation_type
        query = operation.query
        metadata = operation.metadata
        payload = {}

        if not query_id and not query:
            raise ValueError(
                "GraphQL: operation does not specify operation body or id. Invalid GraphQL request"
            )

        feature_switches_list = metadata.feature_switches
        field_toggles_list = metadata.field_toggles
        features = self.get_feature_switches(metadata_features=feature_switches_list)
        field_toggles = self.get_field_toggles(metadata_toggles=field_toggles_list)

        is_query_ready = all([query_id, operation_name, operation_type])
        build_post = operation_type == "mutation" or force_post
        request_payload = {
            "path": self.get_graphql_path(
                query_id=query_id, operation_name=operation_name
            ),
            # "method": "POST" if (is_query_ready and build_post) else "GET",
            "method": "GET" if (is_query_ready and not build_post) else "POST",
            "headers": {**headers, "content-type": "application/json"},
        }

        if timeout is not None:
            request_payload["timeout"] = timeout

        if is_query_ready:
            if build_post:
                payload = self.prepare_post_request(
                    features=features,
                    field_toggles=field_toggles,
                    query=query,
                    query_id=query_id,
                    variables=variables,
                )
            else:
                payload = self.prepare_get_request(
                    features=features, field_toggles=field_toggles, variables=variables
                )
        else:
            if query_id and not operation_name:
                print(
                    f"GraphQL: operation with id {query_id} does not include operation name"
                )
            payload = self.prepare_post_request(
                features=features,
                field_toggles=field_toggles,
                query=query,
                query_id=query_id,
                variables=variables,
            )

        request_payload.update(payload)
        return request_payload


if __name__ == "__main__":
    pass
