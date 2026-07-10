from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional, Type, Union

from tweeterpy.log import Logger
from tweeterpy.schemas.constants import APIVersion, ResponseType
from tweeterpy.schemas.types import TextResponse
from tweeterpy.services.parser import APIParser

if TYPE_CHECKING:
    from tweeterpy.core.abstractions import TweeterPyLogger
    from tweeterpy.core.api import APIClient, AsyncAPIClient


class BaseAPIUpdater:
    def __init__(
        self, logger: Optional[Union[TweeterPyLogger, Type[TweeterPyLogger]]] = None
    ) -> None:
        self.parser = APIParser(logger=logger)
        self.logger = Logger.get_logger(logger=logger, name=__name__)

    def _build_bundle_queue(self, response: str, deep_scan: bool):
        default_bundle_targets = ["main", "api"]
        bundle_queue = {}

        bundle_manifest = self.parser.parse_bundle_manifest(html_content=response)

        # Add default bundles to queue
        for bundle_name in default_bundle_targets:
            bundle = self.parser.get_bundle(
                bundle_name=bundle_name, html_content=response, manifest=bundle_manifest
            )
            if bundle:
                bundle_queue[bundle_name] = bundle

        # Deep Scan: Expand queue with all operational bundles from manifest
        if deep_scan and bundle_manifest:
            operational_bundles_manifest = self.parser.get_operational_bundles(
                manifest=bundle_manifest
            )
            if operational_bundles_manifest:
                bundle_queue.update(operational_bundles_manifest.bundles)

        return bundle_queue

    def _get_base_definitions(self, response: str, deep_scan: bool):
        switches_data = self._extract_feature_switches(response=response)
        bundle_queue = self._build_bundle_queue(response=response, deep_scan=deep_scan)

        return {
            "features": switches_data.get("features", {}),
            "feature_switch": switches_data.get("feature_switch", {}),
            "operations": {},
        }, bundle_queue

    def _extract_feature_switches(self, response: str):
        features = {}
        feature_switch = self.parser.parse_features(html_content=response)

        # Process Feature Switches (Merging Default + User specific)
        if feature_switch:
            default_features = feature_switch.get("defaultConfig") or {}
            user_features = feature_switch.get("user", {}).get("config", {}) or {}
            raw_feature_switches = {**default_features, **user_features}
            features = {
                name: switch.get("value", None) if isinstance(switch, dict) else switch
                for name, switch in raw_feature_switches.items()
            }

        return {"feature_switch": feature_switch, "features": features}


class APIUpdater(BaseAPIUpdater):
    def __init__(
        self,
        api_client: APIClient,
        logger: Optional[Union[TweeterPyLogger, Type[TweeterPyLogger]]] = None,
    ) -> None:
        self.api_client = api_client
        super().__init__(logger=logger)

    def run(self, response: str, deep_scan: bool = False):
        api_definitions, bundle_queue = self._get_base_definitions(
            response=response, deep_scan=deep_scan
        )

        try:
            self.logger.info(
                f"Processing {len(bundle_queue)} bundle/s to extract API Operations..."
            )

            for bundle_name, bundle in bundle_queue.items():
                try:
                    self.logger.debug(
                        f"Processing Bundle: {bundle_name} - {bundle.url}"
                    )
                    js_content: TextResponse = self.api_client.get(
                        endpoint=bundle.url,
                        version=APIVersion.UNVERSIONED,
                        response_type=ResponseType.TEXT,
                    )
                    operations = self.parser.parse_operations(js_content=js_content)
                    if operations:
                        api_definitions["operations"].update(operations)
                except Exception as error:
                    self.logger.warning(f"Error processing {bundle_name}: {error}")

        except Exception as error:
            self.logger.error(f"Error during update: {error}")

        return api_definitions


class AsyncAPIUpdater(BaseAPIUpdater):
    def __init__(
        self,
        api_client: AsyncAPIClient,
        logger: Optional[Union[TweeterPyLogger, Type[TweeterPyLogger]]] = None,
    ) -> None:
        self.api_client = api_client
        super().__init__(logger=logger)

    async def fetch_bundle(
        self, bundle_name: str, bundle_url: str, semaphore: asyncio.Semaphore
    ):
        async with semaphore:
            try:
                self.logger.debug(f"Processing Bundle: {bundle_name} - {bundle_url}")
                js_content: TextResponse = await self.api_client.get(
                    endpoint=bundle_url,
                    version=APIVersion.UNVERSIONED,
                    response_type=ResponseType.TEXT,
                )
                return self.parser.parse_operations(js_content=js_content)
            except Exception as error:
                self.logger.exception(f"Error processing {bundle_name}: {error}")

    async def run(
        self, response: str, deep_scan: bool = False, max_concurrency: int = 10
    ):
        api_definitions, bundle_queue = self._get_base_definitions(
            response=response, deep_scan=deep_scan
        )
        semaphore = asyncio.Semaphore(max_concurrency)

        try:
            self.logger.info(f"Processing {len(bundle_queue)} bundle/s concurrently...")

            # Create all tasks for concurrent execution
            tasks = [
                self.fetch_bundle(
                    bundle_name=bundle_name, bundle_url=bundle.url, semaphore=semaphore
                )
                for bundle_name, bundle in bundle_queue.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for operations in results:
                if not operations or not isinstance(operations, dict):
                    continue
                api_definitions["operations"].update(operations)

        except Exception as error:
            self.logger.error(f"Error during update: {error}")
        return api_definitions


if __name__ == "__main__":
    pass
