import json
import logging.config
from typing import Dict, List, Optional

from tweeterpy.constants import LOGGING_CONFIG
from tweeterpy.core.resources import RegexPatterns, XUrls
from tweeterpy.utils.decorators import ensure_str
from tweeterpy.utils.text import normalize_js_object

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class APIParser:
    BUNDLE_NAME_PREFIXES = ('modules', 'shared~loader',
                            'loader', 'bundle', 'shared~bundle', 'ondemand', 'api')

    BUNDLE_NAME_EXCLUSIONS = ('i18n', 'emoji', 'icons', 'ondemand.countries',
                              'vendors~', 'shared~ui', 'node_modules', 'react-syntax')

    def __init__(self) -> None:
        pass

    def load_json(self, data: str, raise_error: bool = False) -> Optional[Dict]:
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError) as error:
            logger.error(error)
            if raise_error:
                raise error
            return None

    @ensure_str("html_content")
    def find_bundle_url(self, html_content: str, bundle_name: str) -> Optional[str]:
        for match in RegexPatterns.JS_BUNDLES.finditer(html_content):
            if match.group("bundle_name") == bundle_name:
                return match.group(0)
        return None

    @ensure_str("html_content")
    def get_api_bundle_url(self, html_content: str, manifest: Optional[Dict] = None) -> Optional[str]:
        bundle_url = self.get_bundle_url(
            bundle_name="api", html_content=html_content, manifest=manifest)

        if not bundle_url:
            api_match = RegexPatterns.API_BUNDLE.search(html_content)
            if api_match:
                api_bundle_hash = api_match.group('bundle_hash')
                bundle_url = f"{XUrls.TWITTER_CDN}/api.{api_bundle_hash}a.js"

        return bundle_url

    @ensure_str("html_content")
    def get_bundle_url(self, bundle_name: str, html_content: str, manifest: Optional[Dict] = None) -> Optional[str]:
        url_from_source = self.find_bundle_url(
            html_content=html_content, bundle_name=bundle_name)
        if url_from_source:
            return url_from_source

        bundle_manifest = manifest or self.parse_bundle_manifest(
            html_content=html_content)
        bundle_hash = bundle_manifest.get(
            bundle_name) if bundle_manifest else None

        if bundle_hash:
            return f"{XUrls.TWITTER_CDN}/{bundle_name}.{bundle_hash}a.js"

        return None

    def get_operational_bundles(self, manifest: Dict[str, str]) -> List[Dict[str, str]]:
        operational_bundles = []
        for bundle_name, bundle_hash in manifest.items():
            if not bundle_name or not bundle_hash:
                continue

            if not bundle_name.startswith(self.BUNDLE_NAME_PREFIXES):
                continue

            if bundle_name.startswith(self.BUNDLE_NAME_EXCLUSIONS):
                continue

            operational_bundles.append({"bundle_name": bundle_name, "bundle_hash": bundle_hash,
                                       "bundle_url": f"{XUrls.TWITTER_CDN}/{bundle_name}.{bundle_hash}a.js"})

        return operational_bundles

    @ensure_str("html_content")
    def parse_bundle_manifest(self, html_content: str) -> Optional[Dict[str, str]]:
        match = RegexPatterns.BUNDLE_MANIFEST.search(html_content)
        if not match:
            return None

        raw_mapping = match.group("mapping")
        bundle_manifest = self.load_json(
            data=normalize_js_object(raw_mapping), raise_error=False)

        return bundle_manifest

    @ensure_str("html_content")
    def parse_initial_state(self, html_content: str):
        match = RegexPatterns.INITIAL_STATE.search(html_content)
        if not match:
            return None

        return self.load_json(data=match.group("initial_state"), raise_error=False)

    @ensure_str("html_content")
    def parse_meta_data(self, html_content: str):
        match = RegexPatterns.META_DATA.search(html_content)
        if not match:
            return None

        return self.load_json(data=match.group("meta_data"), raise_error=False)

    @ensure_str("html_content")
    def parse_features(self, html_content: str):
        initial_state = self.parse_initial_state(html_content=html_content)
        if isinstance(initial_state, dict) and "featureSwitch" in initial_state:
            return initial_state.get("featureSwitch")

        feature_switch_match = RegexPatterns.FEATURE_SWITCH_OBJECT.search(
            html_content)
        if feature_switch_match:
            feature_switch = feature_switch_match.group("feature_switch")
            return self.load_json(data=feature_switch, raise_error=False)

        return None

    @ensure_str("js_content")
    def parse_operations(self, js_content: str):
        operations = {}

        for match in RegexPatterns.OPERATIONS.finditer(js_content):
            raw_operation = match.group("operation")
            operation = self.load_json(data=normalize_js_object(
                raw_operation), raise_error=False)

            if not operation:
                continue

            query_id = operation.get("queryId")
            operation_name = operation.get("operationName")
            if query_id and operation_name:
                operations[operation_name] = operation

        return operations


if __name__ == "__main__":
    pass
