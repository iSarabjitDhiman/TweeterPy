import logging.config
import re
from http.cookies import SimpleCookie
from typing import Any, Dict
from urllib.parse import urlparse

from x_client_transaction import ClientTransaction

from tweeterpy.config import TweeterPyConfig
from tweeterpy.constants import LOGGING_CONFIG
from tweeterpy.core.abstractions import TweeterPySession
from tweeterpy.core.resources import RegexPatterns, XUrls
from tweeterpy.utils.misc import is_json_response
from tweeterpy.utils.text import to_string, parse_json


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# Request/Response Session Hooks

class BaseHandler:
    """Shared utilities for request and response hooks."""

    @staticmethod
    def get_cookie(session: TweeterPySession, name: str, default: Any = None, **kwargs) -> Any:
        """Safely retrieves a cookie from the session."""
        getter = getattr(session.cookies, "get", lambda n, **k: default)
        return getter(name, **kwargs)

    @staticmethod
    def get_headers(context: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures headers exist and returns a copy to avoid side effects."""
        return context.get("headers", {}).copy()

    @staticmethod
    def set_cookie(session: TweeterPySession, name: str, value: str, **kwargs):
        """Standardizes cookie injection across different session types."""
        setter = getattr(session.cookies, "set", None)
        if setter and callable(setter):
            try:
                setter(name=name, value=value.strip('"'), **kwargs)
            except Exception as error:
                logger.debug(f"Failed to set cookie {name}: {error}")

    @staticmethod
    def update_headers(context: Dict[str, Any], new_headers: Dict[str, Any], overwrite: bool = False) -> Dict[str, Any]:
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
    def inject_twitter_headers(url: str, **context):
        """
        Automatically attaches the Bearer token only to Twitter API and GraphQL endpoints.
        Prevents 403 errors when visiting the main x.com / twitter.com homepages.
        """
        # Matches: api.x.com, x.com/i/api/, x.com/graphql/, etc.
        api_patterns = [r"api\.(x|twitter)\.com",
                        r"(x|twitter)\.com/i/api/", r"/graphql/"]
        is_api_request = any(re.search(pattern, url.lower())
                             for pattern in api_patterns)

        if is_api_request:
            twitter_headers = {
                "authorization": TweeterPyConfig.BEARER_TOKEN,
                "x-twitter-active-user": "yes",
                "x-twitter-client-language": "en"
            }

            return RequestHandlers.update_headers(context=context, new_headers=twitter_headers, overwrite=False)

        return context

    @staticmethod
    def inject_auth_headers(session: TweeterPySession, **context):
        """Injects CSRF and Auth headers if the session is logged in."""
        auth_token = RequestHandlers.get_cookie(
            session=session, name="auth_token")
        csrf_token = RequestHandlers.get_cookie(session=session, name="ct0")

        if auth_token:
            headers = {"x-twitter-auth-type": "OAuth2Session"}
            if csrf_token:
                headers["x-csrf-token"] = str(csrf_token)

            return RequestHandlers.update_headers(context=context, new_headers=headers, overwrite=True)

        return context

    @staticmethod
    def inject_guest_token(session: TweeterPySession, **context):
        """Injects x-guest-token header from the session cookies."""
        guest_token = RequestHandlers.get_cookie(
            session=session, name="gt", domain=".x.com")

        if guest_token:
            return RequestHandlers.update_headers(context=context, new_headers={"x-guest-token": str(guest_token)}, overwrite=False)

        return context

    @staticmethod
    def inject_transaction_id(url: str, method: str, session: TweeterPySession, **context):
        """
        Generates and injects the x-client-transaction-id header.
        Requires session.client_transaction to be initialized.
        """
        client_transaction = getattr(session, "client_transaction", None)

        if isinstance(client_transaction, ClientTransaction):
            try:
                transaction_id = client_transaction.generate_transaction_id(
                    method=method, path=urlparse(url).path)
                if transaction_id:
                    context = RequestHandlers.update_headers(context=context, new_headers={
                                                             "x-client-transaction-id": str(transaction_id)}, overwrite=True)
            except Exception as error:
                logger.warning(
                    f"Could not generate x-client-transaction-id: {error}")

        return {"url": url, "method": method, **context}


class ResponseHandlers(BaseHandler):
    @staticmethod
    def api_error_validator(response: Any, **context):
        """
        Audits the response for HTTP-level and Twitter API-level errors.
        Raises an exception if the API returns an error without data.
        """
        if hasattr(response, "raise_for_status") and callable(response.raise_for_status):
            response.raise_for_status()

        if not is_json_response(response=response):
            return response

        data = parse_json(data=response)
        if not isinstance(data, dict):
            return response

        errors = data.get("errors", [])
        if "error" in data:
            errors.append(data.get("error"))

        # if errors and not data.get("data", None):
        if errors:
            messages = []
            for error in errors:
                code = error.get('code', None)
                message = error.get('message', None)
                messages.append(
                    f"Error code {code} - {message}" if code else message)

            error_message = "\n".join(messages)
            logger.error(f"Twitter API Error: {error_message}")

        return response

    @staticmethod
    def twitter_cookie_injector_hook(response: Any, session: TweeterPySession, **context):
        """Extracts document.cookie calls from Twitter's HTML and manually sets them in the session."""
        if is_json_response(response=response):
            return response

        content = to_string(data=response)

        if not content:
            return response

        for match in RegexPatterns.DOCUMENT_COOKIE.finditer(content):
            cookie_parser = SimpleCookie()
            try:
                cookie_parser.load(match.group("cookie_content"))
                for name, morsel in cookie_parser.items():
                    ResponseHandlers.set_cookie(session=session,
                                                name=name,
                                                value=morsel.value,
                                                domain=morsel.get(
                                                    "domain", ".x.com"),
                                                path=morsel.get("path", "/"))

            except Exception as error:
                logger.warning(error)

        return response

    @staticmethod
    def twitter_guest_token_handler(url: str, response: Any, session: TweeterPySession, **context):
        """Extracts guest_token from JSON responses like activate.json."""
        if not is_json_response(response=response):
            return response

        if XUrls.GUEST_TOKEN in url:
            try:
                data = parse_json(data=response)
                if isinstance(data, dict) and data.get("guest_token", None):
                    ResponseHandlers.set_cookie(session=session,
                                                name="gt",
                                                value=str(
                                                    data.get("guest_token")),
                                                domain=".x.com",
                                                path="/")

            except Exception as error:
                logger.debug(f"Failed to parse guest token JSON: {error}")

        return response


if __name__ == "__main__":
    pass
