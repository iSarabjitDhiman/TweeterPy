import re

from tweeterpy.core.resources import XUrls


class RegexPatterns:
    API_BUNDLE = re.compile(r'api:\s*"(?P<bundle_hash>[^"]+)"')
    BUNDLE_MANIFEST = re.compile(
        r"(?P<assignment>"
        r"[a-z0-9_$]+\.[a-z0-9_$]+\s*=\s*"
        r"(?P<id_var>[a-z0-9_$]+)\s*=>\s*(?P=id_var)\s*"
        r"\+\s*\"\.\"\s*\+\s*"
        r"(?P<mapping>\{[\s\S]*?\})"
        r"\s*\[(?P=id_var)\]\s*"
        r"\+\s*\"a\.js\""
        r")"
    )
    FEATURE_SWITCH_OBJECT = re.compile(
        r'"featureSwitch":\s*(?P<feature_switch>\{'
        r'.*?'
        r'"customOverrides":\s*\{.*?\}'
        r'\s*\})',
        re.DOTALL
    )
    INITIAL_STATE = re.compile(
        r'window\.__INITIAL_STATE__\s*=\s*(?P<initial_state>\{.*?\});', re.DOTALL)
    JS_BUNDLES = re.compile(
        rf'{re.escape(XUrls.TWITTER_CDN)}/(?P<bundle_name>[\w\.~-]+)\.(?P<bundle_hash>[a-f0-9]+)a?\.js', re.IGNORECASE)
    MAIN_JS_BUNDLE = re.compile(
        rf'{re.escape(XUrls.TWITTER_CDN)}/main\.(?P<bundle_hash>[a-f0-9]+)\.js')
    META_DATA = re.compile(
        r'window\.__META_DATA__\s*=\s*(?P<meta_data>\{.*?\});', re.DOTALL)
    OPERATIONS = re.compile(
        r'e\.exports\s*=\s*(?P<operation>\{'
        r'(?=.*?queryId:\s*"(?P<query_id>[^"]+)")'
        r'(?=.*?operationName:\s*"(?P<operation_name>[^"]+)")'
        r'(?=.*?operationType:\s*"(?P<operation_type>[^"]+)")'
        r'.*?\}\s*\})',
        re.DOTALL
    )
    QUERY_ID_VALIDATOR = re.compile(r'^[A-Za-z0-9_\-]+$')
    WORD_BOUNDARY_REGEX = re.compile(
        r'[_.\s-]+|(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')

    # JS_BUNDLES = re.compile(r'https://abs\.twimg\.com/responsive-web/client-web/(?:main|api)\.[a-z0-9]+\.js')
    # MAIN_JS_URL = re.compile(r'https://abs\.twimg\.com/responsive-web/client-web/main\.[a-z0-9]+\.js')
    # OPERATIONS = re.compile(r'\{(?=[^}]*?queryId:"(?P<queryId>[^"]+)")(?=[^}]*?operationName:"(?P<operationName>[^"]+)")(?=[^}]*?operationType:"(?P<operationType>[^"]+)")')
    # OPERATIONS = re.compile(r'\{queryId:"(?P<queryId>[^"]+)",operationName:"(?P<operationName>[^"]+)",operationType:"(?P<operationType>[^"]+)"')
    # FEATURE_SWITCHES = re.compile(r'"(?P<key>[^"]+)":\{value:(?P<val>true|false|"[^"]*"|\d+)\}')


if __name__ == "__main__":
    pass
