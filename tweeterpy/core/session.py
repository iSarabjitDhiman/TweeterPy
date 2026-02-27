from typing import Any, Dict

import curl_cffi

from tweeterpy.config import TweeterPyConfig
from tweeterpy.core.abstractions import HttpMethod, TweeterPySession
from tweeterpy.core.handlers import RequestHandlers, ResponseHandlers


class BaseSession(TweeterPySession):
    def __init__(self, session) -> None:
        super().__init__()

        self._session: Any = session

        self.request_hooks.extend([RequestHandlers.inject_auth_headers,
                                  RequestHandlers.inject_guest_token,
                                  RequestHandlers.inject_twitter_headers,
                                  RequestHandlers.inject_transaction_id])

        self.response_hooks.extend([ResponseHandlers.api_error_validator,
                                    ResponseHandlers.twitter_cookie_injector_hook,
                                    ResponseHandlers.twitter_guest_token_handler])

        self.update_headers(TweeterPyConfig.headers())

    def update_headers(self, headers: Dict[str, Any]):
        self._session.headers.update(headers)

    @property
    def headers(self):
        return self._session.headers

    @property
    def cookies(self):
        return self._session.cookies


class Session(BaseSession):
    def __init__(self) -> None:
        session = curl_cffi.Session(impersonate="chrome")
        super().__init__(session=session)

    def _send(self, url: str, method: HttpMethod, **kwargs):
        return self._session.request(url=url, method=method, **kwargs)


class AsyncSession(BaseSession):
    def __init__(self) -> None:
        session = curl_cffi.AsyncSession(impersonate="chrome")
        super().__init__(session=session)

    async def _send(self, url: str, method: HttpMethod, **kwargs):
        return await self._session.request(url=url, method=method, **kwargs)


if __name__ == "__main__":
    pass
