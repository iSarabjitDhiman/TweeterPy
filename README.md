<h1 align="center">TweeterPy</h1>

<p align="center">
<a href="https://choosealicense.com/licenses/mit/"> <img src="https://img.shields.io/badge/License-MIT-green.svg"></a>
<a href="https://www.python.org/"><img src="https://img.shields.io/pypi/pyversions/tweeterpy"></a>
<a href="https://pypi.org/project/tweeterpy/"> <img src="https://img.shields.io/pypi/v/tweeterpy"></a>
<a href="https://github.com/iSarabjitDhiman/TweeterPy/commits"> <img src="https://img.shields.io/github/last-commit/iSarabjitDhiman/TweeterPy"></a>
<a href="https://twitter.com/isarabjitdhiman"> <img src="https://img.shields.io/twitter/follow/iSarabjitDhiman?style=social"></a>

## Overview

TweeterPy is a python library to extract data from Twitter. TweeterPy API lets you scrape data from a user's profile like username, userid, bio, followers/followings list, profile media, tweets, etc.

> _Note_ : `Use it on Your Own Risk. Scraping with Residential proxies is advisable while extracting data at scale/in bulk. If possible, use multiple accounts to fetch data from Twitter.` **_DON'T USE YOUR PERSONAL ACCOUNT FOR SCRAPING PURPOSES._**

## Installation

Install TweeterPy with pip

```python
  pip install tweeterpy
```

## Usage/Examples

```python
python quickstart.py
```

OR

```python
from twitter import TweeterPy

TweeterPy()
```

> ### Example - Get User ID of a User.

```python
from tweeterpy import TweeterPy

twitter = TweeterPy()

print(twitter.get_user_id('elonmusk'))

```

> ### Example -- Async Version

```python
from tweeterpy import TweeterPy
from tweeterpy import util

twitter = TweeterPy()

# check limits before start using it.
# To check the api rate limits of an endpoint, just set return_rate_limit=True. It works with all methods, below are a few examples.
twitter.get_user_id('',return_rate_limit=True)
twitter.get_friends('',follower=True,return_rate_limit=True)
twitter.get_friends('',following=True,return_rate_limit=True)


# now start using it, its as same as the regular version except it take a list as input.
data = twitter.get_user_id(['elonmusk','user1','user2','user3'])
followers = twitter.get_friends(['elonmusk','user1','user2','user3'],followers=True,total=50)


# if you already have a list of user Ids, I recommend you to use get_multiple_users_data. The get_multiple_users_data method uses a native endpoint which returns user info without making multiple requests.
# Otherwise you can use get_user_info if you have a list of just usernames.
user_data = twitter.get_user_info(['elonmusk','user1','user2','user3'])


# you can also filter the returned data with find_nested_key function from util module.
# Just pass the key to be retrieved
follower_username = util.find_nested_key(followers,"screen_name")
user_ids = util.find_nested_key(data,"screen_name")


# NESTED KEYS AS A TUPLE

# you can also give it direct keys' location as a tuple in a hierarchy order if you know exact locaction or if the dataset has multiple similar keys.

user_tweets = twitter.get_user_tweets("elonmusk",total=50)
# Now say if you want to get tweet creation time which is stored in created_at key.

# you will usually do util.find_nested_key(user_tweets,"created_at") if you take a look at the dataset, there are multiple created_at keys. One is for tweet datetime and other is for user account creation time.

"""
This is the location to tweet creation time.
user_tweets[0]['data'][0]['content']['itemContent']['tweet_results']['result']['legacy']['created_at']

This is the location to user account creation time.
user_tweets[0]['data'][0]['content']['itemContent']['tweet_results']['result']['core']['user_results']['result']['legacy']['created_at']
"""
# So we have to be a bit more specific with our nested_keys. We can pass it as a tuple.

user_account_creation = util.find_nested_key(user_tweets,("user_results","result","legacy","created_at"))

user_tweets_creation = util.find_nested_key(user_tweets,("tweet_results","result","legacy","created_at"))

```

## Documentation

Check out step by step guide.

[Documentation](docs/docs.md)

## Configuration

> ### Example - Config Usage

```python
from tweeterpy import config

config.PROXY = {"http":"127.0.0.1","https":"127.0.0.1"}
config.TIMEOUT = 10

```

Check out configuration docs for the available settings.

[Configurations](docs/config.md)

## Features

- Extracts Tweets
- Extracts User's Followers
- Extracts User's Followings
- Extracts User's Profile Details
- Extracts Twitter Profile Media and so on.

## Authors

- [@iSarabjitDhiman](https://www.github.com/iSarabjitDhiman)

## Feedback

If you have any feedback, please reach out to us at hello@sarabjitdhiman.com or contact me on Social Media @iSarabjitDhiman

## Support

For support, email hello@sarabjitdhiman.com
