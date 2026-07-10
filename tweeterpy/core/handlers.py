from __future__ import annotations

import logging.config
import re
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from x_client_transaction import ClientTransaction

from tweeterpy.config import TweeterPyConfig
from tweeterpy.constants import LOGGING_CONFIG
from tweeterpy.core.resources import RegexPatterns, XEndpoints
from tweeterpy.utils.misc import is_json_response
from tweeterpy.utils.text import parse_json, to_string

if TYPE_CHECKING:
    from tweeterpy.core.abstractions import TweeterPySession
    from tweeterpy.schemas.types import Headers, RequestContext, Response


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# Request/Response Session Hooks


class BaseHandler:
    """Shared utilities for request and response hooks."""

    @staticmethod
    def get_cookie(
        session: TweeterPySession, name: str, default: Any = None, **kwargs
    ) -> Any:
        """Safely retrieves a cookie from the session."""
        getter = getattr(session.cookies, "get", lambda n, **k: default)
        return getter(name, **kwargs)

    @staticmethod
    def get_headers(context: RequestContext) -> Headers:
        """Ensures headers exist and returns a copy to avoid side effects."""
        return (context.get("headers") or {}).copy()

    @staticmethod
    def set_cookie(session: TweeterPySession, name: str, value: str, **kwargs) -> None:
        """Standardizes cookie injection across different session types."""
        setter = getattr(session.cookies, "set", None)
        if setter and callable(setter):
            try:
                setter(name=name, value=value.strip('"'), **kwargs)
            except Exception as error:
                logger.warning(f"Failed to set cookie {name}: {error}")

    @staticmethod
    def update_headers(
        context: RequestContext, new_headers: Headers, overwrite: bool = False
    ) -> RequestContext:
        """
        Updates the headers within the kwargs context.
        If overwrite is False, it only sets headers that don't already exist.
        """
        if not isinstance(new_headers, dict):
            return context

        # Ensure we are working with a copy to avoid mutating the original dict prematurely
        headers = BaseHandler.get_headers(context=context)
        for key, value in new_headers.items():
            if overwrite:
                headers[key] = value
            else:
                headers.setdefault(key, value)

        context["headers"] = headers
        return context


class RequestHandlers(BaseHandler):
    @staticmethod
    def inject_twitter_headers(context: RequestContext) -> RequestContext:
        """
        Automatically attaches the Bearer token only to Twitter API and GraphQL endpoints.
        Prevents 403 errors when visiting the main x.com / twitter.com homepages.
        """
        url = context.get("url")
        if url is None:
            return context

        # Matches: api.x.com, x.com/i/api/, x.com/graphql/, etc.
        api_patterns = [
            r"api\.(x|twitter)\.com",
            r"(x|twitter)\.com/i/api/",
            r"/graphql/",
        ]
        is_api_request = any(
            re.search(pattern, url.lower()) for pattern in api_patterns
        )

        if is_api_request:
            twitter_headers = {
                "authorization": TweeterPyConfig.BEARER_TOKEN,
                "x-twitter-active-user": "yes",
                "x-twitter-client-language": "en",
            }

            return RequestHandlers.update_headers(
                context=context, new_headers=twitter_headers, overwrite=False
            )

        return context

    @staticmethod
    def inject_auth_headers(context: RequestContext) -> RequestContext:
        """Injects CSRF and Auth headers if the session is logged in."""
        session = context.get("session")
        if not session:
            return context

        auth_token = RequestHandlers.get_cookie(session=session, name="auth_token")
        csrf_token = RequestHandlers.get_cookie(session=session, name="ct0")

        headers = {}

        if auth_token:
            headers["x-twitter-auth-type"] = "OAuth2Session"
        if csrf_token:
            headers["x-csrf-token"] = str(csrf_token)

        if headers:
            return RequestHandlers.update_headers(
                context=context, new_headers=headers, overwrite=True
            )

        return context

    @staticmethod
    def inject_guest_token(context: RequestContext) -> RequestContext:
        """Injects x-guest-token header from the session cookies."""
        session = context.get("session")
        if not session:
            return context

        guest_token = RequestHandlers.get_cookie(
            session=session, name="gt", domain=".x.com"
        )

        if guest_token:
            return RequestHandlers.update_headers(
                context=context,
                new_headers={"x-guest-token": str(guest_token)},
                overwrite=False,
            )

        return context

    @staticmethod
    def inject_transaction_id(context: RequestContext) -> RequestContext:
        """
        Generates and injects the x-client-transaction-id header.
        Requires session.client_transaction to be initialized.
        """
        session = context.get("session")
        client_transaction = getattr(session, "client_transaction", None)

        if isinstance(client_transaction, ClientTransaction):
            try:
                transaction_id = client_transaction.generate_transaction_id(
                    method=context.get("method"), path=urlparse(context.get("url")).path
                )
                if transaction_id:
                    return RequestHandlers.update_headers(
                        context=context,
                        new_headers={"x-client-transaction-id": str(transaction_id)},
                        overwrite=True,
                    )
            except Exception as error:
                logger.warning(f"Could not generate x-client-transaction-id: {error}")

        return context


class ResponseHandlers(BaseHandler):
    @staticmethod
    def api_error_validator(response: Response, context: RequestContext) -> Response:
        """
        Audits the response for HTTP-level and Twitter API-level errors.
        Raises an exception if the API returns an error without data.
        """

        if not is_json_response(response=response):
            if hasattr(response, "raise_for_status") and callable(
                response.raise_for_status
            ):
                response.raise_for_status()

            return response

        data = parse_json(data=response)

        if not isinstance(data, dict):
            return response

        errors = data.get("errors", [])
        result_data = data.get("data")

        if "error" in data:
            errors.append(data.get("error"))

        # if errors and not data.get("data", None):
        if errors:
            messages = []
            for error in errors:
                code = error.get("code", None)
                message = error.get("message", None)
                messages.append(f"Error code {code} - {message}" if code else message)

            error_message = "\n".join(messages)
            if not result_data:
                raise RuntimeError(f"Twitter API Error: {error_message}")
            else:
                logger.error(f"Twitter API Error: {error_message}")

        return response

    @staticmethod
    def twitter_cookie_injector_hook(
        response: Response, context: RequestContext
    ) -> Response:
        """Extracts document.cookie calls from Twitter's HTML and manually sets them in the session."""
        session = context.get("session")
        if not session or is_json_response(response=response):
            return response

        content = to_string(data=response)

        if not content:
            return response

        for match in RegexPatterns.DOCUMENT_COOKIE.finditer(content):
            cookie_parser = SimpleCookie()
            try:
                cookie_parser.load(match.group("cookie_content"))
                for name, morsel in cookie_parser.items():
                    ResponseHandlers.set_cookie(
                        session=session,
                        name=name,
                        value=morsel.value,
                        domain=morsel.get("domain", ".x.com"),
                        path=morsel.get("path", "/"),
                    )

            except Exception as error:
                logger.warning(
                    f"Failed to injection parse document cookie segment: {error}"
                )

        return response

    @staticmethod
    def twitter_guest_token_handler(
        response: Response, context: RequestContext
    ) -> Response:
        """Extracts guest_token from JSON responses like activate.json."""
        session = context.get("session")
        url = context.get("url")

        if not session or not all([session, url, is_json_response(response=response)]):
            return response

        url_path = urlparse(url=url).path

        if XEndpoints.GUEST_TOKEN in url_path:
            try:
                data = parse_json(data=response)
                if isinstance(data, dict) and data.get("guest_token", None):
                    ResponseHandlers.set_cookie(
                        session=session,
                        name="gt",
                        value=str(data.get("guest_token")),
                        domain=".x.com",
                        path="/",
                    )

            except Exception as error:
                logger.debug(f"Failed to parse guest token JSON: {error}")

        return response


if __name__ == "__main__":
    pass
