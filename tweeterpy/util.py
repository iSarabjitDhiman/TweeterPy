import datetime
import time
from urllib.parse import urljoin
from .constants import Path
from .constants import PUBLIC_TOKEN
from . import config


class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def generate_headers(session=None):
    headers = {"Authority": Path.DOMAIN,
               "Accept-Encoding": "gzip, deflate, br",
               "Accept-Language": "en-US,en;q=0.9",
               "Authorization": PUBLIC_TOKEN,
               "Cache-Control": "no-cache",
               "Referer": Path.BASE_URL,
               "User-Agent": config._USER_AGENT,
               "X-Twitter-Active-User": "yes",
               "X-Twitter-Client-Language": "en"
               }
    if session:
        if "auth_token" in session.cookies.keys():
            session.get(Path.BASE_URL)
            session.headers.update(
                {"X-Csrf-Token": session.cookies.get("ct0", None), "X-Twitter-Auth-Type": "OAuth2Session"})
    return headers


def generate_features(default_features=True, user_data_features=False, user_info_feautres=False, additional_features=False):
    features = {}
    if default_features:
        default_features = {"responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": True,
                            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                            "responsive_web_graphql_timeline_navigation_enabled": True}
        features.update(default_features)

    if user_data_features or user_info_feautres:
        features.update({"hidden_profile_likes_enabled": False, "highlights_tweets_tab_ui_enabled": True,
                         "creator_subscriptions_tweet_preview_api_enabled": True})
        if user_info_feautres:
            features.update(
                {"subscriptions_verification_info_verified_since_enabled": True})

    if additional_features:
        features.update({"rweb_lists_timeline_redesign_enabled": True, "creator_subscriptions_tweet_preview_api_enabled": True, "tweetypie_unmention_optimization_enabled": True,
                         "responsive_web_edit_tweet_api_enabled": True, "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True, "view_counts_everywhere_api_enabled": True,
                         "longform_notetweets_consumption_enabled": True, "responsive_web_twitter_article_tweet_consumption_enabled": False, "tweet_awards_web_tipping_enabled": False,
                         "freedom_of_speech_not_reach_fetch_enabled": True, "standardized_nudges_misinfo": True, "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
                         "longform_notetweets_rich_text_read_enabled": True, "longform_notetweets_inline_media_enabled": False, "responsive_web_enhance_cards_enabled": False})

    return features


def generate_url(domain=None, url_path=None):
    if not domain and not url_path:
        raise TypeError("URL Path cannot be of NoneType.")
    if not domain:
        domain = Path.API_URL
    return urljoin(domain, url_path)


def check_for_errors(response):
    if isinstance(response, dict) and "errors" in response.keys():
        error_message = "\n".join([error['message']
                                  for error in response['errors']])
        raise Exception(error_message)
    # return response['flow_token'] # For manual Way
    return response


def check_api_rate_limits(response):
    # fmt:off - Code fomatting turned off
    current_time = time.time()
    api_requests_limit = response.headers.get('x-rate-limit-limit')
    remaining_api_requests = response.headers.get('x-rate-limit-remaining')
    limit_reset_timestamp = response.headers.get('x-rate-limit-reset')
    if api_requests_limit is None:
        return
    api_requests_limit, remaining_api_requests, limit_reset_timestamp = map(int, [api_requests_limit, remaining_api_requests, limit_reset_timestamp])
    limit_exhausted = True if remaining_api_requests == 0 else False
    remaining_time_datetime_object = datetime.timedelta(seconds=limit_reset_timestamp - current_time)
    # convert to human readable format
    remaining_time = str(remaining_time_datetime_object).split(':')
    remaining_time = f"{remaining_time[0]} Hours, {remaining_time[1]} Minutes, {float(remaining_time[2]):.2f} Seconds"
    # fmt:on
    api_limit_stats = {"total_limit": api_requests_limit, "remaining_requests_count": remaining_api_requests,
                       "resets_after": remaining_time, "reset_after_datetime_object": remaining_time_datetime_object,
                       "rate_limit_exhausted": limit_exhausted}
    return api_limit_stats


if __name__ == "__main__":
    pass
