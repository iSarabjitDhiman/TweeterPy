from tweeterpy.schemas import Endpoint, Operation
from tweeterpy.utils.misc import DotNotationMeta


class XUrls(metaclass=DotNotationMeta):
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


class XOperations(metaclass=DotNotationMeta):
    @staticmethod
    def _create_operation(slug: str) -> Operation:
        return Operation(endpoint=Endpoint.from_slug(slug=slug))

    # fmt:off
    BIZ_PROFILE_FETCH_USER = _create_operation("6OFpJ3TH3p8JpwOSgfgyhg/BizProfileFetchUser")
    FAVORITERS = _create_operation("mpMee2WCjo7Nm4gRRHHnvA/Favoriters")
    FOLLOWERS = _create_operation("WWFQL1d4gxtqm2mjZCRa-Q/Followers")
    FOLLOWERS_YOU_KNOW = _create_operation("wYAUyD58y1AFol2g2bLqzw/FollowersYouKnow")
    FOLLOWING = _create_operation("OLcddmNLPVXGDgSdSVj0ow/Following")
    HOME_LATEST_TIMELINE = _create_operation("Js4oMnCV2D4gpEocblJ6Tg/HomeLatestTimeline")
    HOME_TIMELINE = _create_operation("ggIgQGz-fN1Z9YBhAoTCVA/HomeTimeline")
    LIKES = _create_operation("QPKcH_nml6UIOxHLjmNsuw/Likes")
    LIST_LATEST_TWEETS_TIMELINE = _create_operation("2Vjeyo_L0nizAUhHe3fKyA/ListLatestTweetsTimeline")
    PROFILE_SPOTLIGHTS_QUERY = _create_operation("9zwVLJ48lmVUk8u_Gh9DmA/ProfileSpotlightsQuery")
    RETWEETERS = _create_operation("7Fwe5A6kE05QIybims116A/Retweeters")
    SEARCH_TIMELINE = _create_operation("IOJ89SDQ9IrZ2t7hSD4Fdg/SearchTimeline")
    TOPIC_LANDING_PAGE = _create_operation("KDCkc4PZY-sCy_L-scQImw/TopicLandingPage")
    TWEET_DETAIL = _create_operation("Pn68XRZwyV9ClrAEmK8rrQ/TweetDetail")
    TWEET_RESULT_BY_REST_ID = _create_operation("0hWvDhmW8YQ-S_ib3azIrw/TweetResultByRestId")
    USER_BY_REST_ID = _create_operation("8slyDObmnUzBOCu7kYZj_A/UserByRestId")
    USERS_BY_REST_IDS = _create_operation("GD4q8bBE2i6cqWw2iT74Gg/UsersByRestIds")
    USER_BY_SCREEN_NAME = _create_operation("qRednkZG-rn1P6b48NINmQ/UserByScreenName")
    USER_HIGHLIGHTS_TWEETS = _create_operation("w9-i9VNm_92GYFaiyGT1NA/UserHighlightsTweets")
    USER_MEDIA = _create_operation("wlwQkva3Zii3b8CJjXSBCw/UserMedia")
    USER_TWEETS = _create_operation("NPgNFbBEhFTul68weP-tYg/UserTweets")
    USER_TWEETS_AND_REPLIES = _create_operation("2dNLofLWl-u8EQPURIAp9w/UserTweetsAndReplies")
    VIEWER = _create_operation("k3027HdkVqbuDPpdoniLKA/Viewer")
    # fmt:on


if __name__ == "__main__":
    pass
