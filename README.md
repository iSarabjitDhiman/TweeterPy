<h1 align="center">TweeterPy</h1>

<p align="center">
<a href="https://choosealicense.com/licenses/mit/"> <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License"></a>
<a href="https://www.python.org/"><img src="https://img.shields.io/pypi/pyversions/tweeterpy" alt="pyversions"></a>
<a href="https://pypi.org/project/tweeterpy/"> <img src="https://img.shields.io/pypi/v/tweeterpy" alt="pypi"></a>
<a href="https://github.com/iSarabjitDhiman/TweeterPy/commits"> <img src="https://img.shields.io/github/last-commit/iSarabjitDhiman/TweeterPy" alt="github"></a>
<a href="https://discord.gg/pHY6CU5Ke4"> <img alt="Discord" src="https://img.shields.io/discord/1149281691479851018?style=flat&logo=discord&logoColor=white"></a>
<a href="https://twitter.com/isarabjitdhiman"> <img src="https://img.shields.io/twitter/follow/iSarabjitDhiman?style=social" alt="twitter"></a>

## Overview

TweeterPy is a python library to extract data from Twitter. TweeterPy API lets you scrape data from a user's profile like username, userid, bio, followers/followings list, profile media, tweets, etc.

> _Note_ : `Use it on Your Own Risk. Scraping with Residential proxies is advisable while extracting data at scale/in bulk. If possible, use multiple accounts to fetch data from Twitter.` **_DON'T USE YOUR PERSONAL ACCOUNT FOR SCRAPING PURPOSES._**

## Installation

Install TweeterPy with pip

```shell
pip install tweeterpy
```

## Usage/Examples

```shell
python quickstart.py
```

OR

```python
from tweeterpy import TweeterPy
# proxy = {'http': 'proxy_here', 'https': 'proxy_here'}
proxy = None
TweeterPy(proxies=proxy, log_level="INFO")
```

> ### Example - Get User ID of a User.

```python
from tweeterpy import TweeterPy

twitter = TweeterPy()

print(twitter.get_user_id('elonmusk'))

```

## Documentation

Check out step-by-step guide.

[Documentation](docs/docs.md)

## Features

- Extracts Tweets
- Extracts User's Followers
- Extracts User's Followings
- Extracts User's Profile Details
- Extracts Twitter Profile Media and much more.

## Authors

- [@iSarabjitDhiman](https://www.github.com/iSarabjitDhiman)

## Feedback

If you have any feedback, please reach out to us at hello@sarabjitdhiman.com or contact me on Social Media @iSarabjitDhiman

## Support

For support, email hello@sarabjitdhiman.com
