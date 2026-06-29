from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Dict, List, Union, cast

from tweeterpy.schemas.types import RequestContext

if TYPE_CHECKING:
    from tweeterpy.core.abstractions import TweeterPySession
    from tweeterpy.schemas.types import RequestHook, Response, ResponseHook


class HookDispatcher:
    """
    Dedicated manager for executing request and response middlewares.
    """

    def __init__(self, session: TweeterPySession) -> None:
        self.session = session

    def _extend_context(
        self, context: Union[Dict[str, Any], RequestContext]
    ) -> RequestContext:
        """Injects the session reference into a shallow copy of the context."""
        return cast(RequestContext, {**context, "session": self.session})

    def run_request_hooks(
        self, hooks: List[RequestHook], initial_context: Dict[str, Any]
    ) -> RequestContext:
        """Runs pre-request hooks to prepare the execution context."""
        context: RequestContext = cast(RequestContext, initial_context)

        for hook in hooks:
            if inspect.iscoroutinefunction(hook):
                raise RuntimeError(
                    f"Cannot run async hook {hook.__name__} in a synchronous session."
                )

            result = hook(context=self._extend_context(context))
            if isinstance(result, dict):
                initial_context.update(result)

        initial_context.pop("session", None)
        return context

    async def run_request_hooks_async(
        self,
        hooks: List[RequestHook],
        initial_context: Dict[str, Any],
    ) -> RequestContext:
        context: RequestContext = cast(RequestContext, initial_context)

        for hook in hooks:
            result = hook(context=self._extend_context(context))
            if inspect.isawaitable(result):
                result = await result

            if isinstance(result, dict):
                initial_context.update(result)

        initial_context.pop("session", None)
        return context

    def run_response_hooks(
        self, hooks: List[ResponseHook], response: Response, context: RequestContext
    ) -> Response:
        """Runs post-request hooks to transform the response object."""
        for hook in hooks:
            if inspect.iscoroutinefunction(hook):
                raise RuntimeError(
                    f"Cannot run async hook {hook.__name__} in a synchronous session."
                )

            # Each hook receives the current response and the context used to get it
            transformed = hook(response=response, context=self._extend_context(context))

            # If the hook returns a value, it becomes the response for the NEXT hook
            if transformed is not None:
                response = transformed
        return response

    async def run_response_hooks_async(
        self, hooks: List[ResponseHook], response: Response, context: RequestContext
    ) -> Response:
        for hook in hooks:
            transformed = hook(response=response, context=self._extend_context(context))

            if inspect.isawaitable(transformed):
                transformed = await transformed

            if transformed is not None:
                response = transformed
        return response


if __name__ == "__main__":
    pass
