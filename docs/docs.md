<h1 align="center">Documentation</h1>

## Import & Initialize.

```python
from tweeterpy import TweeterPy
from tweeterpy import config # if want to change configurations.Check out config docs.

twitter = TweeterPy()
```

> ### Example - Get User ID of a User.

```python
from tweeterpy import TweeterPy
from tweeterpy import config

# Check Configuration docs for the available settings.
# config.PROXY = {"http":"127.0.0.1","https":"127.0.0.1"}
# config.TIMEOUT = 10

twitter = TweeterPy()

# By Deafult it uses a Guest Session.
# Try to fetch data without login first, i.e. with a guest session. Use logged in sessions only if required.


# If you want to use it with logged in session, use any one of the followings to generate a logged in session.

# Multiple Ways of generating Sessions.

> # DON'T USE ALL THREE, JUST USE ANY ONE OF THE FOLLOWINGS.

# twitter.generate_session(auth_token="auth_token_here") #-- Use Auth-Token to Login
# twitter.login("username_here","password_here") #-- Use credentials to login.
# twitter.load_session() #-- Load session from local storage if u previously saved some session with twitter.save_session()

print(twitter.get_user_id('elonmusk'))

```

## Check If User is Logged In.

```python
logged_in()

    """
        Check if the user is logged in.

        Returns:
            bool: Returns True if the user is logged in.
    """
```

## Get Logged In User Details.

```python
self.me

    """
        Returns logged in user information.

        Returns:
            dict: Currently logged in user's data.
    """
```

## Save a Logged In Session

```python
save_session(session=None,session_name=None)
    """
        Save a logged in session to avoid frequent logins in future.

        Args:
            session (requests.Session, optional): requests.Session object you want to save. If None, saves current session by default. Defaults to None.
            session_name (str, optional): Session name. If None, uses currently logged in username. Defaults to None.

        Returns:
            path: Saved session file path.
    """
```

## Restore Session from a Saved Session File

```python
load_session(session_file_path=None,session=None)
    """
        Load a saved session.

        Args:
            session_file_path (path, optional): File path to load session from. If None, shows a list of all saved session to choose from. Defaults to None.
            session (request.Session, optional): requests.Session object to load a saved session into. Defaults to None.

        Returns:
            requests.Session: Restored session.
    """
```

## Generate a New Session (Guest Session OR With an Auth-Toekn)

```python
generate_session(auth_token=None)
    """
        Generate a twitter session. With/Without Login.

        Args:
            auth_token (str, optional): Generate session with an auth-token. If auth_token is None (Default Behaviour), generates a guest session without login. Defaults to None.

        Returns:
            requests.Session: requests.Session Object.
    """
```

## Log into an account

```python
login(username=None, password=None)

    """
        Log into an account.

        Args:
            username (str, optional): Twitter username or email. Defaults to None.
            password (str, optional): Password. Defaults to None.
    """
```

## Get User ID of a Twitter User

```python
get_user_id(username)

    """
        Get user ID of a twitter user.

        Args:
            username (str): Twitter username.

        Returns:
            str: User ID.
    """
```

## Get User Details i.e. username, fullname, bio etc.

```python
get_user_info(user_id)

    """
        Extracts user details like username, userid, bio, website, follower/following count etc.

        Args:
            user_id (str/int): User ID.

        Returns:
            dict: User information.
    """
```

## Get User Details i.e. username, fullname, bio etc. and Verification Badge Details.

```python
get_user_data(username)

    """
        Extracts user details as same as get_user_info method. Except this one returns info about blue tick verification badge as well.

        Args:
            username (str): Twitter username.

        Returns:
            dict: User information.
    """
```

## Get Mutiple Users' Details

```python
get_multiple_users_data(user_ids)

    """
        Get user information of multiple twitter users.

        Args:
            user_ids (list): List of twitter users' IDs.

        Returns:
            list: Multiple users data.
    """

```

## Get User's Tweets

```python
get_user_tweets(user_id, with_replies=False, end_cursor=None, total=None)

    """
        Get Tweets from a user's profile.

        Args:
            user_id (int): User ID.
            with_replies (bool, optional): Set to True if want to get the tweets user replied to, from user's profile page. Defaults to False.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
    """
```

## Get User Media Posts

```python
get_user_media(user_id, end_cursor=None, total=None)

    """
        Get media from a user's profile.

        Args:
            user_id (int): User ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
    """
```

## Get Details of a Tweet Post

```python
get_tweet(tweet_id, with_tweet_replies=False, end_cursor=None, total=None)

    """
        Get Tweets from a user's profile.

        Args:
            tweet_id (int): Tweet ID.
            with_tweet_replies (bool, optional): Set to True if want to get the tweets replies as well. Defaults to False.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Only applicable if with with_tweet_replies is True. Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Tweet data.
    """
```

## Get Tweets Liked by a User -- LOGIN REQUIRED

```python
get_liked_tweets(user_id, end_cursor=None, total=None)

    """
        Get Tweets liked by a user.

        Args:
            user_id (int): User ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
    """
```

## Get Tweets from Home Timeline -- LOGIN REQUIRED

```python
get_user_timeline(end_cursor=None, total=None)

    """
        Get tweets from home timeline (Home Page).

        Args:
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
    """
```

## Get Tweets from a Tweet List (Tweet Lists are Available on Twitter Mobile App)

```python
get_list_tweets(list_id, end_cursor=None, total=None):
    """
        Get tweets from a Tweets List.

        Args:
            list_id (str/int): Tweets List ID. (Can be extracted from twitter mobile app.)
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
    """
```

## Perform a Search

```python
search(search_query, end_cursor=None, total=None, search_filter=None)

    """
        Get search results.

        Args:
            search_query (str): Search term.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) Number of results you want to get. If None, extracts all results. Defaults to None.
            search_filter (str, optional): Type of search you want to perform. Available filters - Latest , Top , People , Photos , Videos. Defaults to 'Top'.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
    """
```

## Get User's Followers/Followings/Mutual Followers -- LOGIN REQUIRED

```python
get_friends(user_id, follower=False, following=False, mutual_follower=False, end_cursor=None, total=None)

    """
        Get User's follower, followings or mutual followers.

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
```

## Check User's Profile Category.

```python
get_profile_business_category(user_id)

    """
        Extracts profile category of a Professional/Business twitter profile. Can also be extracted from get_user_info and get_user_data methods.

        Args:
            user_id (int): User ID.

        Returns:
            dict: User profile category information.
    """

```

## Get List of Users Who Liked The Specified Tweet. -- LOGIN REQUIRED

```python
get_tweet_likes(tweet_id, end_cursor=None, total=None)

    """
        Returns data about the users who liked the given tweet post.

        Args:
            tweet_id (int): Tweet ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
    """
```

## Get List of Users Who Re-Tweeted The Specified Tweet. -- LOGIN REQUIRED

```python
get_retweeters(tweet_id, end_cursor=None, total=None)

    """
        Returs data about the users who retweeted the given tweet post.

        Args:
            tweet_id (int): Tweet ID.
            end_cursor (str, optional): Last endcursor point. (To start from where you left off last time). Defaults to None.
            total (int, optional): Total(Max) number of results you want to get. If None, extracts all results. Defaults to None.

        Returns:
            dict: Returns data, cursor_endpoint, has_next_page
    """
```
