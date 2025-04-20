import json
import random
import getpass
import requests
import logging.config
from functools import reduce
from typing import Union, Dict

from tweeterpy import util
from tweeterpy.login import TaskHandler
from tweeterpy.updater import ApiUpdater
from tweeterpy.tid import ClientTransaction
from tweeterpy.utils.request import RequestClient
from tweeterpy.utils.logging import set_log_level
from tweeterpy.utils.session import load_session, save_session
from tweeterpy.constants import Path, FeatureSwitch, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class TweeterPy:

    def __init__(self, proxies: Dict[str, str] = None, log_level: Union[str, int] = None):
        """TweeterPy constructor

        Args:
            proxies (dict, optional): Proxies to use. Format {"http":"proxy_here","https":"proxy_here"}. Defaults to None.
            log_level (str, optional): Logging level : "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL". Defaults to None.
        """
        if log_level is None:
            log_level = "INFO"

        if proxies and isinstance(proxies, str):
            proxies = {'http': proxies, 'https': proxies}

        self.proxies = proxies
        self.request_client: RequestClient = None

        set_log_level(log_level, external_only=False)
        self.generate_session()

        # update api endpoints
        restore_cache = not util.update_required()
        self.update_api(restore_cache=restore_cache)

    def update_api(self, restore_cache=True):
        """
        Update API Manually

        Args:
            restore_cache (bool, optional): Set whether to restore offline (cached/old) version or online (latest) version of the API data. Defaults to True.
        """
        if self.request_client is None:
            self.generate_session()
        token = self.request_client.session.headers.pop("Authorization")
        try:
            ApiUpdater(request_client=self.request_client,
                       restore_cache=restore_cache)
        except Exception as error:
            logger.warn(error)
        self.request_client.session.headers.update({"Authorization": token})

    def _generate_request_data(self, endpoint, variables=None, **kwargs):
        # fmt: off - Turns off formatting for this block of code. Just for the readability purpose.
        url = util.generate_url(domain=Path.API_URL, url_path=endpoint)
        query_params = {}
        if variables:
            query_params["variables"] = json.dumps(variables)
        if kwargs:
            features = FeatureSwitch().get_query_features(endpoint) or util.generate_features(**kwargs)
            query_params["features"] = json.dumps(features)
        # fmt: on   
        request_payload = {"url": url, "params": query_params}
        logger.debug(f"Request Payload => {request_payload}")
        return request_payload

    def _handle_pagination(self, url, params, end_cursor=None, data_path=None, total=None, pagination=True, **kwargs):
        # fmt: off  - Turns off formatting for this block of code. Just for the readability purpose.
        def filter_data(response):
            filtered_data = []
            for each_entry in response:
                if each_entry['entryId'].startswith('cursor-top') or each_entry['entryId'].startswith('cursor-bottom'):
                    continue
                filtered_data.append(each_entry)
                if total is not None and (len(data_container['data']) + len(filtered_data)) >= total:
                    return filtered_data
            return filtered_data

        if not pagination and total:
            logger.warn("Either enable the pagination or disable total number of results.")
            raise Exception("pagination cannot be disabled while the total number of results are specified.")
        data_container = {"data": [],"cursor_endpoint": None, "has_next_page": True, "api_rate_limit": None}
        while data_container["has_next_page"]:
            try:
                if end_cursor:
                    variables = json.loads(params['variables'])
                    variables['cursor'] = end_cursor
                    params['variables'] = json.dumps(variables)
                response = self.request_client.request(url, params=params)
                data_container['api_rate_limit'] = response.get("api_rate_limit")
                entries = reduce(lambda entry, key: entry.get(key, {}), data_path, response)
                if not entries:
                    return data_container
                data = [item for item in entries if item['type'] == 'TimelineAddEntries'][0]['entries']
                top_cursor = [
                    entry for entry in data if entry['entryId'].startswith('cursor-top')]
                if top_cursor:
                    top_cursor = reduce(dict.get, ('content','value'),top_cursor[0]) or reduce(dict.get, ('content','itemContent','value'),end_cursor[0])
                end_cursor = [
                    entry for entry in data if entry['entryId'].startswith('cursor-bottom')]
                if end_cursor:
                    end_cursor = reduce(dict.get, ('content','value'),end_cursor[0]) or reduce(dict.get, ('content','itemContent','value'),end_cursor[0])
                data_container['data'].extend(filter_data(data))

                print(len(data_container['data']), end="\r")

                if end_cursor:
                    data_container['cursor_endpoint'] = end_cursor

                if ((top_cursor and end_cursor) and len(data) == 2) or ((top_cursor or end_cursor) and len(data) == 1) or (not end_cursor):
                    data_container["has_next_page"] = False

                if not data_container["has_next_page"] or (total is not None and len(data_container['data']) >= total) or not pagination:
                    return data_container
            # fmt: on 
            except ConnectionError as error:
                logger.exception(error)
                continue

            except Exception as error:
                logger.exception(error)
                return data_container

    @property
    def session(self):
        if isinstance(self.request_client, RequestClient):
            return self.request_client.session

    @session.setter
    def session(self, session):
        if not isinstance(session, requests.Session):
            raise Exception("invalid session")
        self.request_client = RequestClient(session=session)

    @property
    def me(self):
        """Returns logged in user information.

        Returns:
            dict: Currently logged in user's data.
        """
        variables = {"withCommunitiesMemberships": True,
                     "withSubscribedTab": True, "withCommunitiesCreation": True}
        request_payload = self._generate_request_data(
            Path.VIEWER_ENDPOINT, variables, user_data_features=True)
        try:
            response = self.request_client.request(**request_payload)
            if not isinstance(response, dict):
                raise Exception(response)
            return response
        except:
            logger.info("Guest Session")
            return

    def login_decorator(original_function):
        def wrapper(self, *args, **kwargs):
            if not self.logged_in():
                logger.warn('User is not authenticated.')
                self.login()
            return original_function(self, *args, **kwargs)
        return wrapper

    def generate_session(self, auth_token=None):
        """Generate a twitter session. With/Without Login.

        Args:
            auth_token (str, optional): Generate session with an auth-token. If auth_token is None (Default Behaviour), generates a guest session without login. Defaults to None.

        Returns:
            requests.Session: requests.Session Object.
        """
        try:
            logger.debug("Trying to generate a new session.")
            self.request_client = RequestClient(session=requests.Session())
            session = self.request_client.session
            if self.proxies:
                session.proxies = self.proxies
                session.verify = False
            session.headers.update(util.generate_headers())
            # home_page = self.request_client.request(Path.BASE_URL)
            home_page = util.handle_x_migration(session=session)
            self.request_client.client_transaction = ClientTransaction(
                home_page_response=home_page)
            try:
                response = self.request_client.request(
                    Path.GUEST_TOKEN_URL, method="POST")
                if not response.get('guest_token'):
                    logger.debug(response)
                guest_token = response.get(
                    'guest_token', util.find_guest_token(home_page))
            except Exception as error:
                logger.error(error)
                raise
            session.headers.update({'X-Guest-Token': guest_token})
            session.cookies.update({'gt': guest_token})
            if auth_token:
                session.cookies.update({'auth_token': auth_token})
                util.generate_headers(session)
        except Exception as error:
            logger.exception(f"Couldn't generate a new session.\n{error}\n")
            raise
        logger.debug("Session has been generated.")
        return self.session

    def save_session(self, session=None, session_name=None, path=None):
        """Save a logged in session to avoid frequent logins in future.

        Args:
            session (requests.Session, optional): requests.Session object you want to save. If None, saves current session by default. Defaults to None. 
            session_name (str, optional): Session name. If None, uses currently logged in username. Defaults to None.
            path (str, optional): Session directory. If None, uses DEFAULT_SESSION_DIRECTORY from constants.py. Defaults to None.

        Returns:
            path: Saved session file path.
        """
        if session is None:
            session = self.request_client.session
        if session_name is None:
            session_name = self.me['data']['viewer']['user_results']['result']['legacy']['screen_name']
        return save_session(filename=session_name, path=path, session=session)

    def load_session(self, path=None):
        """Load a saved session.

        Args:
            path (str, optional): Session file path. If None, shows a list of all saved session to choose from. Defaults to None.

        Returns:
            requests.Session: Restored session.
        """
        session = self.generate_session()
        self.request_client = RequestClient(
            session=load_session(path=path, session=session))
        return self.session

    def logged_in(self):
        """Check if the user is logged in.

        Returns:
            bool: Returns True if the user is logged in.
        """
        if "auth_token" in self.request_client.session.cookies.keys():
            # logger.info('User is authenticated.')
            return True
        return False

    def login(self, username=None, password=None, email=None, phone=None, mfa_secret=None, **kwargs):
        """Log into an account.

        Args:
            username (str, optional): Twitter username. Defaults to None.
            password (str, optional): Password. Defaults to None.
            email (str, optional): Twitter email. Defaults to None.
            phone (str, optional): Twitter phone. Defaults to None.
            mfa_secret (str, optional): Twitter MFA Secret Token to generate TOTP code. Defaults to None.
        """
        self.generate_session()
        if username is None:
            username = str(input("Enter Your Username or Email : ")).strip()
        if password is None:
            password = getpass.getpass()
        TaskHandler(request_client=self.request_client).login(
            username, password, email=email, phone=phone, mfa_secret=mfa_secret, **kwargs)
        util.generate_headers(session=self.request_client.session)
        try:
            user = self.me
            username = util.find_nested_key(user, 'screen_name')
            account_locked = util.find_nested_key(user, 'bounce_location')
            if account_locked and not username:
                raise Exception(
                    "Account logged in but couldn't get the user's details ! Make sure, the given account is working. (Ignore if its working)")
            if username:
                print(f"Welcome {username} : Successfully Logged In.")
        except Exception as error:
            logger.warn(error)

    def get_user_id(self, username):
        """Get user ID of a twitter user.

        Args:
            username (str): Twitter username.

        Returns:
            str: User ID.
        """
        if isinstance(username, int) or username.isnumeric():
            return username
        if not self.logged_in():
            return self.get_user_data(username).get('rest_id')
        request_payload = self._generate_request_data(
            Path.USER_ID_ENDPOINT, {"screen_name": username})
        response = self.request_client.request(**request_payload)
        return response['data']['user_result_by_screen_name']['result']['rest_id']

    @login_decorator
    def get_user_info(self, user_id):
        """Extracts user details like username, userid, bio, website, follower/following count etc.

        Args:
            user_id (str/int): User ID.

        Returns:
            dict: User information.
        """
        user_id = self.get_user_id(user_id)
        variables = {"userId": user_id, "withSafetyModeUserFields": True}
        request_payload = self._generate_request_data(
            Path.USER_INFO_ENDPOINT, variables, user_data_features=True)
        response = self.request_client.request(**request_payload)
        return response['data']['user']['result']

    def get_user_data(self, username):
        """Extracts user details as same as get_user_info method. Except this one returns info about blue tick verification badge as well.

        Args:
            username (str): Twitter username.

        Returns:
            dict: User information.
        """
        variables = {"screen_name": username, "withSafetyModeUserFields": True}
        request_payload = self._generate_request_data(
            Path.USER_DATA_ENDPOINT, variables, user_info_feautres=True)
        response = self.request_client.request(**request_payload)
        return response['data']['user']['result']

    @login_decorator
    def get_multiple_users_data(self, user_ids):
        """Get user information of multiple twitter users.

        Args:
            user_ids (list): List of twitter users' IDs.

        Returns:
            list: Multiple users data.
        """
        variables = {"userIds": user_ids}
        request_payload = self._generate_request_data(
            Path.MULTIPLE_USERS_DATA_ENDPOINT, variables, default_features=True)
        response = self.request_client.request(**request_payload)
        return response['data']['users']

    def get_user_tweets(self, user_id, with_replies=False, end_cursor=None, total=None, pagination=True):
        """Get Tweets from a user's profile.

        Args:
            user_id (int): User ID.
            with_replies (bool, optional): Set to True if want to get the tweets user replied to, from user's profile page. Defaults to False.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        user_id = self.get_user_id(user_id)
        query_endpoint = Path.USER_TWEETS_ENDPOINT
        variables = {"userId": user_id, "count": 100, "includePromotedContent": True,
                     "withQuickPromoteEligibilityTweetFields": True, "withVoice": True, "withV2Timeline": True}
        if with_replies:
            if not self.logged_in():
                self.login()
            variables["count"] = 20
            variables['withCommunity'] = True
            query_endpoint = Path.USER_TWEETS_AND_REPLIES_ENDPOINT
            del variables['withQuickPromoteEligibilityTweetFields']

        request_payload = self._generate_request_data(
            query_endpoint, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline',
                     'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    @login_decorator
    def get_user_media(self, user_id, end_cursor=None, total=None, pagination=True):
        """Get media from a user's profile.

        Args:
            user_id (int): User ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        user_id = self.get_user_id(user_id)
        variables = {"userId": user_id, "count": 100, "includePromotedContent": False,
                     "withClientEventToken": False, "withBirdwatchNotes": False, "withVoice": True, "withV2Timeline": True}
        request_payload = self._generate_request_data(
            Path.USER_MEDIA_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline_v2',
                     'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    def get_tweet(self, tweet_id, with_tweet_replies=False, end_cursor=None, total=None, pagination=True):
        """Get Tweets from a user's profile.

        Args:
            tweet_id (int): Tweet ID.
            with_tweet_replies (bool, optional): Set to True if want to get the tweets replies as well. Defaults to False.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Only applicable if with with_tweet_replies is True. Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Tweet data.
        """
        if end_cursor is not None and not with_tweet_replies:
            logger.exception(
                "Either set with_tweet_replies to True or end_cursor to None.")
            raise
        referer = 'tweet' if with_tweet_replies else random.choice(
            ['profile', 'home'])
        variables = {"focalTweetId": tweet_id, "referrer": referer, "with_rux_injections": False, "includePromotedContent": True,
                     "withCommunity": True, "withQuickPromoteEligibilityTweetFields": True, "withArticleRichContent": False, "withBirdwatchNotes": False,
                     "withVoice": True, "withV2Timeline": True}
        variables = variables if self.logged_in() else {
            "tweetId": tweet_id, "withCommunity": False, "includePromotedContent": False, "withVoice": False}
        request_payload = self._generate_request_data(
            Path.TWEET_DETAILS_ENDPOINT, variables, additional_features=True)
        if not self.logged_in():
            request_payload['url'] = request_payload.get('url').replace(
                Path.TWEET_DETAILS_ENDPOINT, Path.TWEET_DETAILS_BY_ID)
        if with_tweet_replies:
            if not self.logged_in():
                self.login()
            data_path = (
                'data', 'threaded_conversation_with_injections_v2', 'instructions')
            return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)
        return self.request_client.request(**request_payload)

    @login_decorator
    def get_liked_tweets(self, user_id, end_cursor=None, total=None, pagination=True):
        """Get Tweets liked by a user.

        Args:
            user_id (int): User ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        user_id = self.get_user_id(user_id)
        variables = {"userId": user_id, "count": 100, "includePromotedContent": False,
                     "withClientEventToken": False, "withBirdwatchNotes": False, "withVoice": True, "withV2Timeline": True}
        request_payload = self._generate_request_data(
            Path.LIKED_TWEETS_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline_v2',
                     'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    @login_decorator
    def get_user_timeline(self, end_cursor=None, total=None, pagination=True):
        """Get tweets from home timeline (Home Page).

        Args:
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"count": 40, "includePromotedContent": True,
                     "latestControlAvailable": True, "withCommunity": True}
        request_payload = self._generate_request_data(
            Path.HOME_TIMELINE_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'home', 'home_timeline_urt', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    @login_decorator
    def get_list_tweets(self, list_id, end_cursor=None, total=None, pagination=True):
        """Get tweets from a Tweets List.

        Args:
            list_id (str/int): Tweets List ID. (Can be extracted from twitter mobile app.)
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"listId": str(list_id), "count": 100}
        request_payload = self._generate_request_data(
            Path.TWEETS_LIST_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'list', 'tweets_timeline',
                     'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    @login_decorator
    def get_topic_tweets(self, topic_id, end_cursor=None, total=None, pagination=True):
        """Get tweets from a Topic.

        Args:
            topic_id (str/int): Topic ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"rest_id": topic_id, "count": 100}
        request_payload = self._generate_request_data(
            Path.TOPIC_TWEETS_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'topic_by_rest_id', 'topic_page',
                     'body', 'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    @login_decorator
    def search(self, search_query, end_cursor=None, total=None, search_filter=None, pagination=True):
        """Get search results.

        Args:
            search_query (str): Search term.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) Number of results you want to get. If None, extracts all results. Defaults to None.
            search_filter (str, optional): Type of search you want to perform. Available filters - Latest , Top , People , Photos , Videos. Defaults to 'Top'.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        # typed_query, hashtag_click, trend_click, recent_search_click, typeahead_click
        search_filter = "Top" if search_filter is None else search_filter
        # Latest , Top , People , Photos , Videos (Product) - Filter
        variables = {"rawQuery": search_query, "count": 20,
                     "querySource": "typed_query", "product": search_filter}
        request_payload = self._generate_request_data(
            Path.SEARCH_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'search_by_raw_query',
                     'search_timeline', 'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    @login_decorator
    def get_friends(self, user_id, follower=False, following=False, mutual_follower=False, end_cursor=None, total=None, pagination=True):
        """Get User's follower, followings or mutual followers.

        Args:
            user_id (int): User ID.
            follower (bool, optional): Set to True if want to extract User's follower. Defaults to False.
            following (bool, optional): Set to True if want to extract User's following. Defaults to False.
            mutual_followers (bool, optional): Set to True if want to extract mutual follower. Defaults to False.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        if (not follower and not following and not mutual_follower) or (follower and following and mutual_follower):
            logger.exception(
                "Set one of the (follower,following,mutual_follower) to True.")
            raise
        user_id = self.get_user_id(user_id)
        query_path = Path.FOLLOWERS_ENDPOINT if follower else Path.FOLLOWINGS_ENDPOINT if following else Path.MUTUAL_FOLLOWERS_ENDPOINT if mutual_follower else None
        variables = {"userId": user_id, "count": 100,
                     "includePromotedContent": False}
        request_payload = self._generate_request_data(
            query_path, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline',
                     'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    @login_decorator
    def get_profile_business_category(self, user_id):
        """Extracts profile category of a Professional/Business twitter profile. Can also be extracted from get_user_info and get_user_data methods.

        Args:
            user_id (int): User ID.

        Returns:
            dict: User profile category information.
        """
        user_id = self.get_user_id(user_id)
        variables = {"rest_id": user_id}
        request_payload = self._generate_request_data(
            Path.PROFILE_CATEGORY_ENDPOINT, variables)
        response = self.request_client.request(**request_payload)
        return response

    @login_decorator
    def get_tweet_likes(self, tweet_id, end_cursor=None, total=None, pagination=True):
        """Returns data about the users who liked the given tweet post.

        Args:
            tweet_id (int): Tweet ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"tweetId": str(tweet_id), "count": 100,
                     "includePromotedContent": True}
        request_payload = self._generate_request_data(
            Path.TWEET_LIKES_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'favoriters_timeline', 'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    @login_decorator
    def get_retweeters(self, tweet_id, end_cursor=None, total=None, pagination=True):
        """Returs data about the users who retweeted the given tweet post.

        Args:
            tweet_id (int): Tweet ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"tweetId": str(tweet_id), "count": 100,
                     "includePromotedContent": True}
        request_payload = self._generate_request_data(
            Path.RETWEETED_BY_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'retweeters_timeline', 'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)

    def get_user_highlights(self, user_id, end_cursor=None, total=None, pagination=True):
        """Get highlights from a user's profile.

        Args:
            user_id (int): User ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.
            pagination (bool, optional): Set to False if want to handle each page request manually. Use end_cursor from the previous page/request to navigate to the next page. Defaults to True.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        user_id = self.get_user_id(user_id)
        variables = {"userId": user_id, "count": 100,
                     "includePromotedContent": True, "withVoice": True}
        request_payload = self._generate_request_data(
            Path.USER_HIGHLIGHTS_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline',
                     'timeline', 'instructions')
        return self._handle_pagination(**request_payload, end_cursor=end_cursor, data_path=data_path, total=total, pagination=pagination)


if __name__ == "__main__":
    pass
