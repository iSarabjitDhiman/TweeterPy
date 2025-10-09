import os
import re
import bs4
import time
import datetime
import tempfile
import logging.config
from functools import reduce
from typing import Dict, List
from urllib.parse import urljoin
from x_client_transaction.utils import get_ondemand_file_url
from tweeterpy.constants import Path, PUBLIC_TOKEN, LOGGING_CONFIG, USER_AGENT, API_TMP_FILE
from dataclasses import dataclass, field, fields, asdict, _MISSING_TYPE

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class RateLimitError(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "Rate limit exceeded."
        super().__init__(message)


def generate_headers(session=None, custom_headers=None):
    headers = {"authority": Path.DOMAIN,
               "accept-language": "en-US,en;q=0.9",
               "cache-control": "no-cache",
               "referer": Path.BASE_URL,
               "user-agent": USER_AGENT,
               "x-twitter-active-user": "yes",
               "x-twitter-client-language": "en"
               }
    if custom_headers and isinstance(custom_headers, dict):
        headers.update(custom_headers)
    if session:
        headers.update({"authorization": PUBLIC_TOKEN})
        headers.update(dict(session.headers))
        if "auth_token" in session.cookies.keys():
            session.get(Path.BASE_URL)
            csrf_token = session.cookies.get("ct0", None)
            headers.update({"x-csrf-token": csrf_token,
                            "x-twitter-auth-type": "OAuth2Session"})
        session.headers.update(headers)
    return headers


def generate_features(default_features=True, user_data_features=False, user_info_feautres=False, additional_features=False):
    features = {}
    if default_features:
        default_features = {"responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": True,
                            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                            "responsive_web_graphql_timeline_navigation_enabled": True}
        features.update(default_features)

    if user_data_features or user_info_feautres:
        features.update({"hidden_profile_likes_enabled": False, "hidden_profile_subscriptions_enabled": True, "highlights_tweets_tab_ui_enabled": True,
                         "responsive_web_twitter_article_notes_tab_enabled": False, "creator_subscriptions_tweet_preview_api_enabled": True})
        if user_info_feautres:
            features.update(
                {"subscriptions_verification_info_is_identity_verified_enabled": True, "subscriptions_verification_info_verified_since_enabled": True})

    if additional_features:
        features.update({"rweb_lists_timeline_redesign_enabled": True, "creator_subscriptions_tweet_preview_api_enabled": True, "c9s_tweet_anatomy_moderator_badge_enabled": True, "tweetypie_unmention_optimization_enabled": True,
                         "responsive_web_edit_tweet_api_enabled": True, "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True, "view_counts_everywhere_api_enabled": True,
                         "longform_notetweets_consumption_enabled": True, "responsive_web_twitter_article_tweet_consumption_enabled": False, "tweet_awards_web_tipping_enabled": False,
                         "freedom_of_speech_not_reach_fetch_enabled": True, "standardized_nudges_misinfo": True, "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False, "rweb_video_timestamps_enabled": True,
                         "longform_notetweets_rich_text_read_enabled": True, "longform_notetweets_inline_media_enabled": False, "responsive_web_media_download_video_enabled": False, "responsive_web_enhance_cards_enabled": False})

    return features


def generate_url(domain=None, url_path=None):
    if not domain and not url_path:
        raise TypeError("URL Path cannot be of NoneType.")
    if not domain:
        domain = Path.API_URL
    return urljoin(domain, url_path)


def find_guest_token(page_source):
    guest_token_regex = re.compile(r"""gt=(\d+);""", re.VERBOSE)
    guest_token_match = re.search(guest_token_regex, str(page_source))
    if not guest_token_match:
        raise Exception("Couldn't find guest token")
    guest_token = guest_token_match.group(1)
    return guest_token


def get_ondemand_file_response(session, home_page):
    ondemand_file_url = get_ondemand_file_url(response=home_page)
    ondemand_file = session.request(url=ondemand_file_url, method="GET")
    ondemand_file_response = ondemand_file.text
    return ondemand_file_response


def handle_x_migration(session):
    home_page = None
    migration_redirection_regex = re.compile(
        r"""(http(?:s)?://(?:www\.)?(twitter|x){1}\.com(/x)?/migrate([/?])?tok=[a-zA-Z0-9%\-_]+)+""", re.VERBOSE)
    try:
        response = session.request(method="GET", url=Path.BASE_URL)
        home_page = bs4.BeautifulSoup(response.content, 'lxml')
        migration_url = home_page.select_one("meta[http-equiv='refresh']")
        migration_redirection_url = re.search(migration_redirection_regex, str(
            migration_url)) or re.search(migration_redirection_regex, str(response.content))
        if migration_redirection_url:
            response = session.request(
                method="GET", url=migration_redirection_url.group(0))
            home_page = bs4.BeautifulSoup(response.content, 'lxml')
        migration_form = home_page.select_one("form[name='f']") or home_page.select_one(
            f"form[action='{Path.X_MIGRATE_URL}']")
        if migration_form:
            url = migration_form.attrs.get("action", Path.X_MIGRATE_URL)
            method = migration_form.attrs.get("method", "POST")
            request_payload = {input_field.get("name"): input_field.get(
                "value") for input_field in migration_form.select("input")}
            response = session.request(
                method=method, url=url, data=request_payload)
            home_page = bs4.BeautifulSoup(response.content, 'lxml')
    except Exception as error:
        logger.error(error)
    finally:
        generate_headers(session=session)
        return home_page


def check_for_errors(response):
    if not isinstance(response, dict):
        return response

    errors = response.get("errors", [])
    if "error" in response:
        errors.append(response.get("error"))

    if errors and not response.get("data"):
        error_message = "\n".join([f"Error code {error.get('code')} - {error.get('message')}" if error.get(
            'code') else error.get('message') for error in errors if error])
        raise Exception(error_message)

    return response


def check_api_rate_limits(response):
    # fmt:off - Code fomatting turned off
    try:
        current_time = time.time()
        api_requests_limit = response.headers.get('x-rate-limit-limit')
        remaining_api_requests = response.headers.get('x-rate-limit-remaining')
        limit_reset_timestamp = response.headers.get('x-rate-limit-reset')
        if api_requests_limit is None:
            return None
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
        logger.debug(api_limit_stats)
        return api_limit_stats
    except:
        return None


def find_nested_key(dataset=None, nested_key=None):
    def get_nested_data(dataset, nested_key, placeholder):
        if isinstance(dataset, list) or isinstance(dataset, dict) and dataset:
            if isinstance(dataset, list):
                for item in dataset:
                    get_nested_data(item, nested_key, placeholder)
            if isinstance(dataset, dict):
                if isinstance(nested_key, tuple) and nested_key[0] in dataset.keys():
                    placeholder.append(reduce(lambda data, key: data.get(key, {}) if isinstance(data, dict) else {},
                                              nested_key, dataset) or None)
                    placeholder.remove(None) if None in placeholder else ''
                    # placeholder.append(reduce(dict.get,nested_key,dataset))
                if isinstance(nested_key, str) and nested_key in dataset.keys():
                    placeholder.append(dataset.get(nested_key))
                for item in dataset.values():
                    get_nested_data(item, nested_key, placeholder)
        if len(placeholder) == 1:
            return placeholder[0]
        return placeholder

    if isinstance(nested_key, list):
        if isinstance(dataset, list):
            return [{key: get_nested_data(data, key, []) for key in nested_key} for data in dataset]
        return {key: get_nested_data(dataset, key, []) for key in nested_key}

    return [get_nested_data(data, nested_key, []) for data in dataset] if isinstance(dataset, list) else get_nested_data(dataset, nested_key, [])


def update_required():
    try:
        current_time = datetime.datetime.now()
        api_backup_file = os.path.join(tempfile.gettempdir(), API_TMP_FILE)
        last_modified = os.path.getmtime(api_backup_file)
        yesterday_time = current_time - datetime.timedelta(hours=24)
        one_day_elapsed = yesterday_time.timestamp() > last_modified
        if one_day_elapsed:
            return True
        return False
    except Exception as error:
        logger.warn(error)
        return True


@dataclass
class _Item:
    # Base Item class for other data-classes to manipulate data.
    _dataset: dict = field(default=None, init=True, repr=False)

    # def __post_init__(self):
    #     for field in fields(self):
    #         if not isinstance(field.default, dataclasses._MISSING_TYPE) and not isinstance(getattr(self, field.name), field.type):
    #             raise ValueError(f'Expected [{field.name}] to be {field.type}, 'f'got {type(getattr(self,field.name))}')

    def load_data(self, direct_keys=None, complex_keys=None, legacy_path=None, dataset_path=None):
        """_summary_

        Args:
            direct_keys (list, optional): One-level nested keys. Defaults to None.
            legacy_path (tuple/str, optional): Path to legacy dataset in nested dict. Defaults to None.
            dataset_path (tuple/str, optional): Path to the original dataset where useful data is stored. Defaults to None.
            complex_keys (dict, optional): Multi-level nested keys. Its better to specify the exact path as there can be duplicates as well. Defaults to None.
        """
        # fmt:off
        if self._dataset and isinstance(self._dataset, dict):
            legacy_dataset = find_nested_key(self._dataset,legacy_path) if legacy_path else None
            original_dataset = find_nested_key(self._dataset,dataset_path) if dataset_path else self._dataset
            for dataset in [legacy_dataset,original_dataset]:
                if dataset is None or not isinstance(dataset,dict):
                    continue
                if complex_keys and isinstance(complex_keys,dict):
                    for item_key, path in complex_keys.items():
                        setattr(self, item_key, find_nested_key(dataset, path)) if not getattr(self, item_key) else ''
                for field in fields(self):
                    if field.name in complex_keys.keys():
                        continue
                    initial_value = getattr(self, field.name)
                    if (not isinstance(field.default, _MISSING_TYPE) and initial_value == field.default) or not isinstance(field.default_factory, _MISSING_TYPE) :
                        key = field.name
                        value = dataset.get(key, None) if key in direct_keys else find_nested_key(dataset, key)
                        value = initial_value if isinstance(value, list) and not value else value
                        setattr(self, field.name, value)
            delattr(self, "_dataset")
        # fmt:on

    def dict(self):
        data = asdict(self)
        data.pop('_dataset')
        return data


@dataclass
class User(_Item):
    can_dm: bool = None
    created_at: str = None
    creator_subscriptions_count: int = None
    default_profile: bool = None
    default_profile_image: bool = None
    description: str = None
    description_urls: List[Dict] = field(default_factory=list)
    favourites_count: int = None
    followers_count: int = None
    friends_count: int = None
    has_custom_timelines: bool = None
    has_graduated_access: bool = None
    id: str = None
    is_blue_verified: bool = None
    is_profile_translatable: bool = None
    is_translator: bool = None
    listed_count: int = None
    location: str = None
    media_count: int = None
    name: str = None
    pinned_tweet_ids_str: List[str] = field(default_factory=list)
    possibly_sensitive: bool = None
    professional_type: str = None
    profile_banner_url: str = None
    profile_image_shape: str = None
    profile_image_url_https: str = None
    profile_interstitial_type: str = None
    profile_url: str = None
    rest_id: str = None
    screen_name: str = None
    statuses_count: int = None
    translator_type: str = None
    url: str = None
    urls: List[Dict] = field(default_factory=list)
    verification_info: dict = None
    verified: bool = None
    verified_phone_status: bool = None
    verified_type: str = None
    withheld_in_countries: List[str] = field(default_factory=list)

    def __post_init__(self):
        user_result = find_nested_key(
            self._dataset, ("user_results", "result"))
        self._dataset = user_result or self._dataset
        custom_keys = {"urls": ("entities", "url", "urls"),
                       "description_urls": ("entities", "description", "urls")}
        self.load_data(direct_keys=['id', 'rest_id', 'description', 'url'],
                       legacy_path="legacy", complex_keys=custom_keys)
        profile_url = f"{Path.BASE_URL}{self.screen_name}" if self.screen_name else None
        setattr(self, "profile_url", profile_url)


@dataclass
class Tweet(_Item):
    bookmark_count: int = None
    bookmarked: bool = None
    conversation_id_str: str = None
    created_at: str = None
    favorite_count: int = None
    favorited: bool = None
    full_text: str = None
    hashtags: List[str] = field(default_factory=list)
    id_str: str = None
    in_reply_to_screen_name: str = None
    in_reply_to_status_id_str: str = None
    in_reply_to_user_id_str: str = None
    is_quote_status: bool = None
    is_translatable: bool = None
    lang: str = None
    name: str = None
    original_tweet: str = None
    possibly_sensitive: bool = None
    possibly_sensitive_editable: bool = None
    quote_count: int = None
    reply_count: int = None
    rest_id: str = None
    retweet_count: int = None
    retweeted: bool = None
    screen_name: str = None
    source: str = None
    tweet_url: str = None
    user_id_str: str = None
    user_mentions: List[Dict] = field(default_factory=list)
    views: dict = field(default_factory=dict)

    def __post_init__(self):
        is_status = find_nested_key(self._dataset, ("tweetResult", "result"))
        legacy_path = (
            "tweetResult" if is_status else "tweet_results", "result", "legacy")
        dataset_path = (
            "tweetResult" if is_status else "tweet_results", "result")
        custom_keys = {"screen_name": ("core", "user_results", "result", "legacy", "screen_name"), "name": (
            "core", "user_results", "result", "legacy", "name")}
        self.load_data(direct_keys=['id_str', 'rest_id', 'source', 'is_translatable', 'possibly_sensitive', 'views', 'created_at'],
                       legacy_path=legacy_path, dataset_path=dataset_path, complex_keys=custom_keys)
        setattr(self, "tweet_url",
                f"{Path.BASE_URL}{self.screen_name}/status/{self.rest_id}")
        setattr(self, "original_tweet",
                f"{Path.BASE_URL}{self.in_reply_to_screen_name}/status/{self.in_reply_to_status_id_str}") if self.in_reply_to_screen_name else ''


if __name__ == "__main__":
    pass
