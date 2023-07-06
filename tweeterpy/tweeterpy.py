import requests
import json
import random
import getpass
from functools import reduce

from .api_util import ApiUpdater
from .constants import Path, FeatureSwitch
from .login_util import TaskHandler
from .request_util import make_request
from .session_util import load_session, save_session
from . import util
from . import config


class TweeterPy:

    def __init__(self):
        self.generate_session()
        # update api endpoints
        ApiUpdater()

    def _generate_request_data(self, endpoint, variables=None, **kwargs):
        # fmt: off - Turns off formatting for this block of code. Just for the readability purpose.
        url = util.generate_url(domain=Path.API_URL, url_path=endpoint)
        query_params = {"variables": json.dumps({**variables})}
        if kwargs:
            features = FeatureSwitch().get_query_features(endpoint) or util.generate_features(**kwargs)
            query_params["features"] = json.dumps(features)
        # fmt: on   
        return url, query_params

    def _handle_pagination(self, url, query_params, end_cursor=None, data_path=None, total=None):
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

        data_container = {"data": [],"cursor_endpoint": None, "has_next_page": True}
        while data_container["has_next_page"]:
            try:
                if end_cursor:
                    varaibles = json.loads(query_params['variables'])
                    varaibles['cursor'] = end_cursor
                    query_params['variables'] = json.dumps(varaibles)
                response = make_request(url, params=query_params)
                data = [item for item in reduce(
                    dict.get, data_path, response) if item['type'] == 'TimelineAddEntries'][0]['entries']
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

                if not data_container["has_next_page"] or (total is not None and len(data_container['data']) >= total):
                    return data_container
            # fmt: on 
            except ConnectionError as error:
                print(error)
                continue

            except Exception as error:
                print(error)
                return data_container

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session):
        self._session = session
        config._DEFAULT_SESSION = session

    @property
    def me(self):
        """Returns logged in user information.

        Returns:
            dict: Currently logged in user's data.
        """
        url = util.generate_url(url_path=Path.VIEWER_ENDPOINT)
        query = {"variables": json.dumps({"withCommunitiesMemberships": True,
                                          "withSubscribedTab": True, "withCommunitiesCreation": True}),
                 "features": json.dumps(util.generate_features())}
        response = self.session.get(url, params=query).json()
        return response

    def login_decorator(original_function):
        def wrapper(self, *args, **kwargs):
            if not self.logged_in():
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
        self.session = requests.Session()
        if config.PROXY is not None:
            self.session.proxies = config.PROXY
            self.session.verify = False
        self.session.headers.update(util.generate_headers())
        make_request(Path.BASE_URL, session=self.session)
        guest_token = make_request(
            Path.GUEST_TOKEN_URL, method="POST", session=self.session)['guest_token']
        self.session.headers.update({'X-Guest-Token': guest_token})
        self.session.cookies.update({'gt': guest_token})
        if auth_token:
            self.session.cookies.update({'auth_token': auth_token})
            util.generate_headers(self.session)
        return self.session

    def save_session(self, session=None, session_name=None):
        """Save a logged in session to avoid frequent logins in future.

        Args:
            session (requests.Session, optional): requests.Session object you want to save. If None, saves current session by default. Defaults to None. 
            session_name (str, optional): Session name. If None, uses currently logged in username. Defaults to None.

        Returns:
            path: Saved session file path.
        """
        if session is None:
            session = self.session
        if session_name is None:
            session_name = self.me['data']['viewer']['user_results']['result']['legacy']['screen_name']
        return save_session(filename=session_name, session=session)

    def load_session(self, session_file_path=None, session=None):
        """Load a saved session.

        Args:
            session_file_path (path, optional): File path to load session from. If None, shows a list of all saved session to choose from. Defaults to None.
            session (request.Session, optional): requests.Session object to load a saved session into. Defaults to None.

        Returns:
            requests.Session: Restored session.
        """
        self.session = load_session(
            file_path=session_file_path, session=session)
        return self.session

    def logged_in(self):
        """Check if the user is logged in.

        Returns:
            bool: Returns True if the user is logged in.
        """
        if "auth_token" in self.session.cookies.keys():
            return True
        return False

    def login(self, username=None, password=None):
        """Log into an account.

        Args:
            username (str, optional): Twitter username or email. Defaults to None.
            password (str, optional): Password. Defaults to None.
        """
        if username is None:
            username = str(input("Enter Your Username or Email : ")).strip()
        if password is None:
            password = getpass.getpass()
        TaskHandler().login(username, password)
        util.generate_headers(session=self.session)

    @login_decorator
    def get_user_id(self, username):
        """Get user ID of a twitter user.

        Args:
            username (str): Twitter username.

        Returns:
            str: User ID.
        """
        if isinstance(username, int) or username.isnumeric():
            return username
        url, query_params = self._generate_request_data(
            Path.USER_ID_ENDPOINT, {"screen_name": username})
        response = make_request(url, params=query_params)
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
        url, query_params = self._generate_request_data(
            Path.USER_INFO_ENDPOINT, variables, user_data_features=True)
        response = make_request(url, params=query_params)
        return response['data']['user']['result']

    @login_decorator
    def get_user_data(self, username):
        """Extracts user details as same as get_user_info method. Except this one returns info about blue tick verification badge as well.

        Args:
            username (str): Twitter username.

        Returns:
            dict: User information.
        """
        variables = {"screen_name": username, "withSafetyModeUserFields": True}
        url, query_params = self._generate_request_data(
            Path.USER_DATA_ENDPOINT, variables, user_info_feautres=True)
        response = make_request(url, params=query_params)
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
        url, query_params = self._generate_request_data(
            Path.MULTIPLE_USERS_DATA_ENDPOINT, variables, default_features=True)
        response = make_request(url, params=query_params)
        return response['data']['users']

    @login_decorator
    def get_user_tweets(self, user_id, with_replies=False, end_cursor=None, total=None):
        """Get Tweets from a user's profile.

        Args:
            user_id (int): User ID.
            with_replies (bool, optional): Set to True if want to get the tweets user replied to, from user's profile page. Defaults to False.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        user_id = self.get_user_id(user_id)
        query_endpoint = Path.USER_TWEETS_ENDPOINT
        variables = {"userId": user_id, "count": 100, "includePromotedContent": True,
                     "withQuickPromoteEligibilityTweetFields": True, "withVoice": True, "withV2Timeline": True}
        if with_replies:
            variables["count"] = 20
            variables['withCommunity'] = True
            query_endpoint = Path.USER_TWEETS_AND_REPLIES_ENDPOINT
            del variables['withQuickPromoteEligibilityTweetFields']

        url, query_params = self._generate_request_data(
            query_endpoint, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline_v2',
                     'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

    @login_decorator
    def get_user_media(self, user_id, end_cursor=None, total=None):
        """Get media from a user's profile.

        Args:
            user_id (int): User ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        user_id = self.get_user_id(user_id)
        variables = {"userId": user_id, "count": 100, "includePromotedContent": False,
                     "withClientEventToken": False, "withBirdwatchNotes": False, "withVoice": True, "withV2Timeline": True}
        url, query_params = self._generate_request_data(
            Path.USER_MEDIA_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline_v2',
                     'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

    @login_decorator
    def get_tweet(self, tweet_id, with_tweet_replies=False, end_cursor=None, total=None):
        """Get Tweets from a user's profile.

        Args:
            tweet_id (int): Tweet ID.
            with_tweet_replies (bool, optional): Set to True if want to get the tweets replies as well. Defaults to False.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Only applicable if with with_tweet_replies is True. Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Tweet data.
        """
        if end_cursor is not None and not with_tweet_replies:
            raise Exception(
                "Either set with_tweet_replies to True or end_cursor to None.")
        referer = 'tweet' if with_tweet_replies else random.choice(
            ['profile', 'home'])
        variables = {"focalTweetId": tweet_id, "referrer": referer, "with_rux_injections": False, "includePromotedContent": True,
                     "withCommunity": True, "withQuickPromoteEligibilityTweetFields": True, "withArticleRichContent": False, "withBirdwatchNotes": False,
                     "withVoice": True, "withV2Timeline": True}
        url, query_params = self._generate_request_data(
            Path.TWEET_DETAILS_ENDPOINT, variables, additional_features=True)
        data_path = (
            'data', 'threaded_conversation_with_injections_v2', 'instructions')
        if with_tweet_replies:
            return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)
        return make_request(url, params=query_params)

    @login_decorator
    def get_liked_tweets(self, user_id, end_cursor=None, total=None):
        """Get Tweets liked by a user.

        Args:
            user_id (int): User ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        user_id = self.get_user_id(user_id)
        if not self.logged_in():
            self.login()
        variables = {"userId": user_id, "count": 100, "includePromotedContent": False,
                     "withClientEventToken": False, "withBirdwatchNotes": False, "withVoice": True, "withV2Timeline": True}
        url, query_params = self._generate_request_data(
            Path.LIKED_TWEETS_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline_v2',
                     'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

    @login_decorator
    def get_user_timeline(self, end_cursor=None, total=None):
        """Get tweets from home timeline (Home Page).

        Args:
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        if not self.logged_in():
            self.login()
        variables = {"count": 40, "includePromotedContent": True,
                     "latestControlAvailable": True, "withCommunity": True}
        url, query_params = self._generate_request_data(
            Path.HOME_TIMELINE_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'home', 'home_timeline_urt', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

    @login_decorator
    def get_list_tweets(self, list_id, end_cursor=None, total=None):
        """Get tweets from a Tweets List.

        Args:
            list_id (str/int): Tweets List ID. (Can be extracted from twitter mobile app.)
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"listId": list_id, "count": 100}
        url, query_params = self._generate_request_data(
            Path.TWEETS_LIST_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'list', 'tweets_timeline',
                     'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

    @login_decorator
    def get_topic_tweets(self, topic_id, end_cursor=None, total=None):
        """Get tweets from a Topic.

        Args:
            topic_id (str/int): Topic ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"rest_id": topic_id, "count": 100}
        url, query_params = self._generate_request_data(
            Path.TOPIC_TWEETS_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'topic_by_rest_id', 'topic_page',
                     'body', 'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

    @login_decorator
    def search(self, search_query, end_cursor=None, total=None, search_filter=None):
        """Get search results.

        Args:
            search_query (str): Search term.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) Number of results you want to get. If None, extracts all results. Defaults to None.
            search_filter (str, optional): Type of search you want to perform. Available filters - Latest , Top , People , Photos , Videos. Defaults to 'Top'.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        search_filter = "Top" if search_filter is None else search_filter
        # Latest , Top , People , Photos , Videos (Product) - Filter
        variables = {"rawQuery": search_query, "count": 20,
                     "querySource": "hashtag_click", "product": search_filter}
        url, query_params = self._generate_request_data(
            Path.SEARCH_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'search_by_raw_query',
                     'search_timeline', 'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

    @login_decorator
    def get_friends(self, user_id, follower=False, following=False, mutual_follower=False, end_cursor=None, total=None):
        """Get User's follower, followings or mutual followers.

        Args:
            user_id (int): User ID.
            follower (bool, optional): Set to True if want to extract User's follower. Defaults to False.
            following (bool, optional): Set to True if want to extract User's following. Defaults to False.
            mutual_followers (bool, optional): Set to True if want to extract mutual follower. Defaults to False.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        if (not follower and not following and not mutual_follower) or (follower and following and mutual_follower):
            raise Exception(
                "Set one of the (follower,following,mutual_follower) to True.")
        user_id = self.get_user_id(user_id)
        if not self.logged_in():
            self.login()
        query_path = Path.FOLLOWERS_ENDPOINT if follower else Path.FOLLOWINGS_ENDPOINT if following else Path.MUTUAL_FOLLOWERS_ENDPOINT if mutual_follower else None
        variables = {"userId": user_id, "count": 100,
                     "includePromotedContent": False}
        url, query_params = self._generate_request_data(
            query_path, variables, additional_features=True)
        data_path = ('data', 'user', 'result', 'timeline',
                     'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

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
        url, query_params = self._generate_request_data(
            Path.PROFILE_CATEGORY_ENDPOINT, variables)
        response = make_request(url, params=query_params)
        return response

    @login_decorator
    def get_tweet_likes(self, tweet_id, end_cursor=None, total=None):
        """Returns data about the users who liked the given tweet post.

        Args:
            tweet_id (int): Tweet ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        if not self.logged_in():
            self.login()
        variables = {"tweetId": str(tweet_id), "count": 100,
                     "includePromotedContent": True}
        url, query_params = self._generate_request_data(
            Path.TWEET_LIKES_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'favoriters_timeline', 'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)

    @login_decorator
    def get_retweeters(self, tweet_id, end_cursor=None, total=None):
        """Returs data about the users who retweeted the given tweet post.

        Args:
            tweet_id (int): Tweet ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        if not self.logged_in():
            self.login()
        variables = {"tweetId": str(tweet_id), "count": 100,
                     "includePromotedContent": True}
        url, query_params = self._generate_request_data(
            Path.RETWEETED_BY_ENDPOINT, variables, additional_features=True)
        data_path = ('data', 'retweeters_timeline', 'timeline', 'instructions')
        return self._handle_pagination(url, query_params, end_cursor=end_cursor, data_path=data_path, total=total)


if __name__ == "__main__":
    pass
