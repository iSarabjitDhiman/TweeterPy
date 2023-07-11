import httpx
import json
import random
import getpass

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

    def get_rate_limits(self, func):
        return callable(getattr(self, str(func))("")(return_rate_limit=True))

    def _generate_request_data(self, endpoint, default_variables=None, custom_variables=None, pagination=None, features=None, return_payload=False, **kwargs):
        # fmt: off - Turns off formatting for this block of code. Just for the readability purpose.
        method = kwargs.pop("method",None) or "GET"
        default_variables = default_variables or {}
        url = kwargs.pop("url",None) or Path.API_URL
        url = util.generate_url(domain=url, url_path=endpoint)
        query_params = {}
        if features:
            features = FeatureSwitch().get_query_features(endpoint) or util.generate_features(features)
            query_params.update({"features":json.dumps(features)})
        if custom_variables and isinstance(custom_variables,dict):
            key,values = custom_variables.popitem()
            values = values[0] if isinstance(values,list) and len(values) == 1 else values
            if isinstance(values,list):
                variables = [json.dumps(default_variables | {key:str(each_item)}) for each_item in values]
                query_params = [query_params | {"variables":each_item} for each_item in variables]
            else:
                variables = json.dumps(default_variables | {key:str(values)})
                query_params = query_params | {"variables": variables}
        else:
            variables = json.dumps(default_variables)
            query_params = query_params | {"variables": variables}
        request_payload = {"method": method, "url": url, "params": query_params}
        # fmt: on   
        if return_payload:
            return request_payload
        if pagination:
            request_payload.update({"pagination_data": pagination})
        return make_request(request_payload=request_payload, **kwargs)

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
        proxies = config.PROXY or None
        ssl_verify = False if proxies else True
        timeout = config.TIMEOUT or 10
        self.session = httpx.Client(
            follow_redirects=True, timeout=timeout, proxies=proxies, verify=ssl_verify)
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
    def get_user_id(self, username, **kwargs):
        """Get user ID of a twitter user.

        Args:
            username (str): Twitter username.

        Returns:
            str: User ID.
        """
        if not isinstance(username, list):
            username = [username]
        user_ids = [*filter(lambda user: user if isinstance(
            user, int) or user.isnumeric() else None, username)]
        if len(user_ids) != len(username):
            pending_users = [user for user in username if user not in user_ids]
            response = self._generate_request_data(
                Path.USER_ID_ENDPOINT, custom_variables={"screen_name": pending_users}, **kwargs)
            user_ids = [*user_ids, *util.find_nested_key(response, "rest_id")]
        return user_ids if len(user_ids) > 1 else user_ids[0] if user_ids else None

    @login_decorator
    def get_user_info(self, user_id, **kwargs):
        """Extracts user details like username, userid, bio, website, follower/following count etc.

        Args:
            user_id (str/int): User ID.

        Returns:
            dict: User information.
        """
        user_id = self.get_user_id(user_id)
        variables = {"withSafetyModeUserFields": True}
        variables_data = {"userId": user_id}
        return self._generate_request_data(
            Path.USER_INFO_ENDPOINT, default_variables=variables, custom_variables=variables_data, features="user_data", **kwargs)

    @login_decorator
    def get_user_data(self, username, **kwargs):
        """Extracts user details as same as get_user_info method. Except this one returns info about blue tick verification badge as well.

        Args:
            username (str): Twitter username.

        Returns:
            dict: User information.
        """
        variables = {"withSafetyModeUserFields": True}
        variables_data = {"screen_name": username}
        return self._generate_request_data(
            Path.USER_DATA_ENDPOINT, default_variables=variables, custom_variables=variables_data, features="user_info", **kwargs)

    @login_decorator
    def get_multiple_users_data(self, user_ids, **kwargs):
        """Get user information of multiple twitter users.

        Args:
            user_ids (list): List of twitter users' IDs.

        Returns:
            list: Multiple users data.
        """
        variables = {"userIds": user_ids}
        user_ids = self.get_user_id(user_ids)
        return self._generate_request_data(
            Path.MULTIPLE_USERS_DATA_ENDPOINT, default_variables=variables, default_features=True, **kwargs)

    @login_decorator
    def get_user_tweets(self, user_id, with_replies=False, end_cursor=None, total=None, **kwargs):
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
        variables = {"count": 100, "includePromotedContent": True,
                     "withQuickPromoteEligibilityTweetFields": True, "withVoice": True, "withV2Timeline": True}
        variables_data = {"userId": user_id}
        if with_replies:
            variables["count"] = 20
            variables['withCommunity'] = True
            query_endpoint = Path.USER_TWEETS_AND_REPLIES_ENDPOINT
            del variables['withQuickPromoteEligibilityTweetFields']
        pagination_data = {"end_cursor": end_cursor, "total": total}

        return self._generate_request_data(query_endpoint, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_user_media(self, user_id, end_cursor=None, total=None, **kwargs):
        """Get media from a user's profile.

        Args:
            user_id (int): User ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        user_id = self.get_user_id(user_id)
        variables = {"count": 100, "includePromotedContent": False,
                     "withClientEventToken": False, "withBirdwatchNotes": False, "withVoice": True, "withV2Timeline": True}
        variables_data = {"userId": user_id}
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(
            Path.USER_MEDIA_ENDPOINT, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_tweet(self, tweet_id, with_tweet_replies=False, end_cursor=None, total=None, **kwargs):
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
        variables = {"referrer": referer, "with_rux_injections": False, "includePromotedContent": True,
                     "withCommunity": True, "withQuickPromoteEligibilityTweetFields": True, "withArticleRichContent": False, "withBirdwatchNotes": False,
                     "withVoice": True, "withV2Timeline": True}
        variables_data = {"focalTweetId": tweet_id}
        pagination_data = {"end_cursor": end_cursor,
                           "total": total} if with_tweet_replies else {}
        return self._generate_request_data(Path.TWEET_DETAILS_ENDPOINT, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_liked_tweets(self, user_id, end_cursor=None, total=None, **kwargs):
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
        variables = {"count": 100, "includePromotedContent": False,
                     "withClientEventToken": False, "withBirdwatchNotes": False, "withVoice": True, "withV2Timeline": True}
        variables_data = {"userId": user_id}
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(Path.LIKED_TWEETS_ENDPOINT, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_user_timeline(self, end_cursor=None, total=None, **kwargs):
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
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(
            Path.HOME_TIMELINE_ENDPOINT, default_variables=variables, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_list_tweets(self, list_id, end_cursor=None, total=None, **kwargs):
        """Get tweets from a Tweets List.

        Args:
            list_id (str/int): Tweets List ID. (Can be extracted from twitter mobile app.)
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"count": 100}
        variables_data = {"listId": list_id}
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(
            Path.TWEETS_LIST_ENDPOINT, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_topic_tweets(self, topic_id, end_cursor=None, total=None, **kwargs):
        """Get tweets from a Topic.

        Args:
            topic_id (str/int): Topic ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
        """
        variables = {"count": 100}
        variables_data = {"rest_id": topic_id}
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(
            Path.TOPIC_TWEETS_ENDPOINT, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def search(self, search_query, end_cursor=None, total=None, search_filter=None, **kwargs):
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
        variables = {"count": 20,
                     "querySource": "hashtag_click", "product": search_filter}
        variables_data = {"rawQuery": search_query}
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(
            Path.SEARCH_ENDPOINT, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_friends(self, user_id, follower=False, following=False, mutual_follower=False, end_cursor=None, total=None, **kwargs):
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
        variables = {"count": 100,
                     "includePromotedContent": False}
        variables_data = {"userId": user_id}
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(
            query_path, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_profile_business_category(self, user_id, **kwargs):
        """Extracts profile category of a Professional/Business twitter profile. Can also be extracted from get_user_info and get_user_data methods.

        Args:
            user_id (int): User ID.

        Returns:
            dict: User profile category information.
        """
        user_id = self.get_user_id(user_id)
        variables_data = {"rest_id": user_id}
        return self._generate_request_data(
            Path.PROFILE_CATEGORY_ENDPOINT, custom_variables=variables_data, **kwargs)

    @login_decorator
    def get_tweet_likes(self, tweet_id, end_cursor=None, total=None, **kwargs):
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
        variables = {"count": 100,
                     "includePromotedContent": True}
        variables_data = {"tweetId": tweet_id}
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(
            Path.TWEET_LIKES_ENDPOINT, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)

    @login_decorator
    def get_retweeters(self, tweet_id, end_cursor=None, total=None, **kwargs):
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
        variables = {"count": 100,
                     "includePromotedContent": True}
        variables_data = {"tweetId": tweet_id}
        pagination_data = {"end_cursor": end_cursor, "total": total}
        return self._generate_request_data(
            Path.RETWEETED_BY_ENDPOINT, default_variables=variables, custom_variables=variables_data, pagination=pagination_data, features="additional", **kwargs)


if __name__ == "__main__":
    pass
