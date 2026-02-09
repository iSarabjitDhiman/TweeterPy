import logging.config
from pathlib import Path

logger = logging.getLogger(__name__)

CURRENT_DIRECTORY = Path(__file__).resolve().parent
BASE_DIRECTORY = CURRENT_DIRECTORY.parent

PACKAGE_NAME = CURRENT_DIRECTORY.name

PUBLIC_TOKEN = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'

# Filename to store api data/endpoints as a backup.
API_TMP_FILE = "tweeterpy_api.json"

# Directory path/name to save and load logged in sessions/cookies. Default path is current directory. i.e. current_path/Twitter Saved Sessions
DEFAULT_SESSION_DIRECTORY = "Twitter Saved Sessions"

FEATURE_SWITCHES_PRESET = {
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "hidden_profile_likes_enabled": False,
    "hidden_profile_subscriptions_enabled": True,
    "highlights_tweets_tab_ui_enabled": True,
    "responsive_web_twitter_article_notes_tab_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "subscriptions_verification_info_verified_since_enabled": True,
    "subscriptions_verification_info_is_identity_verified_enabled": True,
    "rweb_lists_timeline_redesign_enabled": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "tweetypie_unmention_optimization_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": False,
    "tweet_awards_web_tipping_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
    "rweb_video_timestamps_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": False,
    "responsive_web_media_download_video_enabled": False,
    "responsive_web_enhance_cards_enabled": False
}


# File name to save logs.
LOG_FILE_NAME = "tweeterpy.log"

# Logging level : "DEBUG","INFO","WARNING","ERROR","CRITICAL"
# If None, "INFO" will be used for Stream/Console logs and "DEBUG" will be used for file logs.
# LOG_LEVEL = "INFO"
LOG_LEVEL = "INFO"

# Log Configuration.
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] [Line No. %(lineno)d] %(name)s : %(funcName)s :: %(message)s'
        },
        'custom': {
            # 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            'class': 'tweeterpy.utils.logging.CustomFormatter',
        }
    },
    'handlers': {
        'stream': {
            'level': LOG_LEVEL,
            'formatter': 'custom',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_NAME,
            "encoding": "utf-8"
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['stream', 'file'],
            'level': 'DEBUG'
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['stream', 'file'],
            'level': 'DEBUG',
        }
    }
}


class Color:
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW_2 = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    RESET = "\033[0m"


class FeatureSwitch:
    # Data will be added automatically upon API update (Manipulated by ApiUpdater in api_util.py).
    all_feature_switches = {}
    api_endpoints = {}

    def get_query_features(self, api_path):
        # fmt: off 
        try:
            features = self.api_endpoints.get(api_path)['metadata']['featureSwitches']
            features = {feature : self.all_feature_switches.get(feature,{}).get('value',False) for feature in features}
            return features
        # fmt: on
        except:
            logger.warn("Couldn't generate features for request variables.")
            return None


if __name__ == "__main__":
    pass
