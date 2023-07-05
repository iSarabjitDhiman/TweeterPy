PUBLIC_TOKEN = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'


class Path:
    # Data will be updated automatically upon API update (Manipulated by ApiUpdater from api_util.py).
    # URLS
    DOMAIN = "twitter.com"
    BASE_URL = "https://www.twitter.com/"
    API_URL = "https://twitter.com/i/api/graphql/"
    TASK_URL = "https://api.twitter.com/1.1/onboarding/task.json"
    GUEST_TOKEN_URL = "https://api.twitter.com/1.1/guest/activate.json"
    JAVSCRIPT_INSTRUMENTATION_URL = "https://twitter.com/i/js_inst"
    TWITTER_CDN = "https://abs.twimg.com/responsive-web/client-web"
    HOME_TIMELINE_GUEST_URL = "https://twitter.com/i/api/2/guide.json"
    # ENDPOINTS
    HOME_TIMELINE_ENDPOINT = "ggIgQGz-fN1Z9YBhAoTCVA/HomeTimeline"
    HOME_LATEST_TIMELINE_ENDPOINT = "Js4oMnCV2D4gpEocblJ6Tg/HomeLatestTimeline"
    USER_ID_ENDPOINT = "9zwVLJ48lmVUk8u_Gh9DmA/ProfileSpotlightsQuery"
    USER_INFO_ENDPOINT = "8slyDObmnUzBOCu7kYZj_A/UserByRestId"
    USER_DATA_ENDPOINT = "qRednkZG-rn1P6b48NINmQ/UserByScreenName"
    MULTIPLE_USERS_DATA_ENDPOINT = "GD4q8bBE2i6cqWw2iT74Gg/UsersByRestIds"
    USER_MEDIA_ENDPOINT = "wlwQkva3Zii3b8CJjXSBCw/UserMedia"
    USER_TWEETS_ENDPOINT = "NPgNFbBEhFTul68weP-tYg/UserTweets"
    USER_TWEETS_AND_REPLIES_ENDPOINT = "2dNLofLWl-u8EQPURIAp9w/UserTweetsAndReplies"
    TWEETS_LIST_ENDPOINT = "2Vjeyo_L0nizAUhHe3fKyA/ListLatestTweetsTimeline"
    TOPIC_TWEETS_ENDPOINT = "KDCkc4PZY-sCy_L-scQImw/TopicLandingPage"
    TWEET_DETAILS_ENDPOINT = "Pn68XRZwyV9ClrAEmK8rrQ/TweetDetail"
    VIEWER_ENDPOINT = "k3027HdkVqbuDPpdoniLKA/Viewer"
    SEARCH_ENDPOINT = "IOJ89SDQ9IrZ2t7hSD4Fdg/SearchTimeline"
    FOLLOWERS_ENDPOINT = "WWFQL1d4gxtqm2mjZCRa-Q/Followers"
    FOLLOWINGS_ENDPOINT = "OLcddmNLPVXGDgSdSVj0ow/Following"
    MUTUAL_FOLLOWERS_ENDPOINT = "wYAUyD58y1AFol2g2bLqzw/FollowersYouKnow"
    LIKED_TWEETS_ENDPOINT = "QPKcH_nml6UIOxHLjmNsuw/Likes"
    PROFILE_CATEGORY_ENDPOINT = "6OFpJ3TH3p8JpwOSgfgyhg/BizProfileFetchUser"
    TWEET_LIKES_ENDPOINT = "mpMee2WCjo7Nm4gRRHHnvA/Favoriters"
    RETWEETED_BY_ENDPOINT = "7Fwe5A6kE05QIybims116A/Retweeters"


class FeatureSwitch:
    # Data will be added automatically upon API update (Manipulated by ApiUpdater from api_util.py).
    all_feature_switches = {}
    api_endpoints = {}

    def get_query_features(self, api_path):
        # fmt: off 
        try:
            features = self.api_endpoints.get(api_path)['metadata']['featureSwitches']
            features = {feature : self.all_feature_switches.get(feature)['value'] for feature in features}
            return features
        # fmt: on
        except:
            return None


if __name__ == "__main__":
    pass
