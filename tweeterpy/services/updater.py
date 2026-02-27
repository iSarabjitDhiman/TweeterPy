import asyncio
import logging.config

from tweeterpy.constants import LOGGING_CONFIG
from tweeterpy.core.abstractions import TweeterPySession
from tweeterpy.services.parser import APIParser

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class APIUpdater:
    def __init__(self, session: TweeterPySession) -> None:
        self.session = session
        self.parser = APIParser()

    def _prepare_queue(self, response: str, deep_scan: bool) -> tuple[dict, dict]:
        """Shared logic to extract features and build the URL queue."""
        feature_switches = {}
        default_bundle_targets = ["main", "api"]
        bundle_queue = {}

        features = self.parser.parse_features(html_content=response)
        bundle_manifest = self.parser.parse_bundle_manifest(html_content=response)

        # Process Feature Switches (Merging Default + User specific)
        if features:
            default_features = features.get("defaultConfig") or {}
            user_features = features.get("user", {}).get("config", {}) or {}
            raw_feature_switches = {**default_features, **user_features}
            feature_switches = {
                feature_name: feature_switch.get("value", None)
                if isinstance(feature_switch, dict)
                else feature_switch
                for feature_name, feature_switch in raw_feature_switches.items()
            }

        # Add default bundles to queue
        for bundle_name in default_bundle_targets:
            bundle_url = self.parser.get_bundle_url(
                bundle_name=bundle_name, html_content=response, manifest=bundle_manifest
            )
            if bundle_url:
                bundle_queue[bundle_name] = bundle_url

        # Deep Scan: Expand queue with all operational bundles from manifest
        if deep_scan and bundle_manifest:
            operational_bundles = self.parser.get_operational_bundles(
                manifest=bundle_manifest
            )
            if operational_bundles:
                bundle_queue.update(
                    {
                        bundle.get("bundle_name"): bundle.get("bundle_url")
                        for bundle in operational_bundles
                        if isinstance(bundle, dict)
                    }
                )

        return feature_switches, bundle_queue

    async def fetch_bundle(self, bundle_name: str, bundle_url: str):
        try:
            logger.debug(f"Processing Bundle: {bundle_name} - {bundle_url}")

            js_content = await self.session.request(url=bundle_url, method="GET")
            return self.parser.parse_operations(js_content=js_content)
        except Exception as error:
            logger.exception(f"Error processing {bundle_name}: {error}")

    def run(self, response: str, deep_scan: bool = False):
        api_definitions = {"features": {}, "operations": {}}
        try:
            feature_switches, bundle_queue = self._prepare_queue(
                response=response, deep_scan=deep_scan
            )
            api_definitions["features"] = feature_switches

            logger.info(
                f"Processing {len(bundle_queue)} bundle/s to extract API Operations..."
            )

            for bundle_name, bundle_url in bundle_queue.items():
                try:
                    logger.debug(f"Processing Bundle: {bundle_name} - {bundle_url}")
                    js_content = self.session.request(url=bundle_url, method="GET")
                    operations = self.parser.parse_operations(js_content=js_content)
                    if operations:
                        api_definitions["operations"].update(operations)
                except Exception as error:
                    logger.warning(f"Error processing {bundle_name}: {error}")

        except Exception as error:
            logger.error(f"Error during update: {error}")

        return api_definitions

    async def run_async(self, response: str, deep_scan: bool = False):
        api_definitions = {"features": {}, "operations": {}}
        try:
            feature_switches, bundle_queue = self._prepare_queue(
                response=response, deep_scan=deep_scan
            )
            api_definitions["features"] = feature_switches

            logger.info(f"Processing {len(bundle_queue)} bundle/s concurrently...")

            # Create all tasks for concurrent execution
            tasks = [
                self.fetch_bundle(bundle_name=bundle_name, bundle_url=bundle_url)
                for bundle_name, bundle_url in bundle_queue.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for operations in results:
                if not operations or not isinstance(operations, dict):
                    continue
                api_definitions["operations"].update(operations)

        except Exception as error:
            logger.error(f"Error during update: {error}")
        return api_definitions


if __name__ == "__main__":
    pass
