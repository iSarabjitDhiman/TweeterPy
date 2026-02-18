import re
from dataclasses import dataclass, asdict

from tweeterpy.schemas import Endpoint, Operation


@dataclass
class XFeatures:
    # fmt:off
    responsive_web_graphql_exclude_directive_enabled: bool = True
    verified_phone_label_enabled: bool = True
    responsive_web_graphql_skip_user_profile_image_extensions_enabled: bool = False
    responsive_web_graphql_timeline_navigation_enabled: bool = True
    hidden_profile_likes_enabled: bool = False
    hidden_profile_subscriptions_enabled: bool = True
    highlights_tweets_tab_ui_enabled: bool = True
    responsive_web_twitter_article_notes_tab_enabled: bool = False
    creator_subscriptions_tweet_preview_api_enabled: bool = True
    subscriptions_verification_info_verified_since_enabled: bool = True
    subscriptions_verification_info_is_identity_verified_enabled: bool = True
    rweb_lists_timeline_redesign_enabled: bool = True
    c9s_tweet_anatomy_moderator_badge_enabled: bool = True
    tweetypie_unmention_optimization_enabled: bool = True
    responsive_web_edit_tweet_api_enabled: bool = True
    graphql_is_translatable_rweb_tweet_is_translatable_enabled: bool = True
    view_counts_everywhere_api_enabled: bool = True
    longform_notetweets_consumption_enabled: bool = True
    responsive_web_twitter_article_tweet_consumption_enabled: bool = False
    tweet_awards_web_tipping_enabled: bool = False
    freedom_of_speech_not_reach_fetch_enabled: bool = True
    standardized_nudges_misinfo: bool = True
    tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled: bool = False
    rweb_video_timestamps_enabled: bool = True
    longform_notetweets_rich_text_read_enabled: bool = True
    longform_notetweets_inline_media_enabled: bool = False
    responsive_web_media_download_video_enabled: bool = False
    responsive_web_enhance_cards_enabled: bool = False
    # fmt:on

    def to_dict(self):
        return asdict(self)


class XOperations:
    @staticmethod
    def _create_operation(slug: str) -> Operation:
        return Operation(endpoint=Endpoint.from_slug(slug=slug))

    # fmt:off
    BizProfileFetchUser = _create_operation("6OFpJ3TH3p8JpwOSgfgyhg/BizProfileFetchUser")
    Favoriters = _create_operation("mpMee2WCjo7Nm4gRRHHnvA/Favoriters")
    Followers = _create_operation("WWFQL1d4gxtqm2mjZCRa-Q/Followers")
    FollowersYouKnow = _create_operation("wYAUyD58y1AFol2g2bLqzw/FollowersYouKnow")
    Following = _create_operation("OLcddmNLPVXGDgSdSVj0ow/Following")
    HomeLatestTimeline = _create_operation("Js4oMnCV2D4gpEocblJ6Tg/HomeLatestTimeline")
    HomeTimeline = _create_operation("ggIgQGz-fN1Z9YBhAoTCVA/HomeTimeline")
    Likes = _create_operation("QPKcH_nml6UIOxHLjmNsuw/Likes")
    ListLatestTweetsTimeline = _create_operation("2Vjeyo_L0nizAUhHe3fKyA/ListLatestTweetsTimeline")
    ProfileSpotlightsQuery = _create_operation("9zwVLJ48lmVUk8u_Gh9DmA/ProfileSpotlightsQuery")
    Retweeters = _create_operation("7Fwe5A6kE05QIybims116A/Retweeters")
    SearchTimeline = _create_operation("IOJ89SDQ9IrZ2t7hSD4Fdg/SearchTimeline")
    TopicLandingPage = _create_operation("KDCkc4PZY-sCy_L-scQImw/TopicLandingPage")
    TweetDetail = _create_operation("Pn68XRZwyV9ClrAEmK8rrQ/TweetDetail")
    TweetResultByRestId = _create_operation("0hWvDhmW8YQ-S_ib3azIrw/TweetResultByRestId")
    UserByRestId = _create_operation("8slyDObmnUzBOCu7kYZj_A/UserByRestId")
    UsersByRestIds = _create_operation("GD4q8bBE2i6cqWw2iT74Gg/UsersByRestIds")
    UserByScreenName = _create_operation("qRednkZG-rn1P6b48NINmQ/UserByScreenName")
    UserHighlightsTweets = _create_operation("w9-i9VNm_92GYFaiyGT1NA/UserHighlightsTweets")
    UserMedia = _create_operation("wlwQkva3Zii3b8CJjXSBCw/UserMedia")
    UserTweets = _create_operation("NPgNFbBEhFTul68weP-tYg/UserTweets")
    UserTweetsAndReplies = _create_operation("2dNLofLWl-u8EQPURIAp9w/UserTweetsAndReplies")
    Viewer = _create_operation("k3027HdkVqbuDPpdoniLKA/Viewer")
    # fmt:on


class XUrls:
    DOMAIN = "x.com"
    BASE = f"https://{DOMAIN}"
    API_BASE = f"https://api.{DOMAIN}"
    GRAPHQL_BASE = f"{API_BASE}/graphql"
    GUEST_TOKEN = f"{API_BASE}/1.1/guest/activate.json"
    HOME_TIMELINE_GUEST = f"{BASE}/i/api/2/guide.json"
    JAVSCRIPT_INSTRUMENTATION = "https://twitter.com/i/js_inst"
    TASK = f"{API_BASE}/1.1/onboarding/task.json"
    TWITTER_CDN = "https://abs.twimg.com/responsive-web/client-web"
    X_MIGRATION = f"{BASE}/x/migrate"


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
