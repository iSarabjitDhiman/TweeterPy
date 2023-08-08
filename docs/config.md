<h1 align="center">Configuration</h1>

# Importing

```python
from tweeterpy import config
```

> ### Example - Config Usage

```python
from tweeterpy import TweeterPy
from tweeterpy import config

config.PROXY = {"http":"127.0.0.1","https":"127.0.0.1"}
config.TIMEOUT = 10

twitter = TweeterPy()

print(twitter.get_user_id('elonmusk'))

```

## Request Timeout

```python
# request timeout - in seconds
config.TIMEOUT = 5
```

## Using Proxies

```python
# Example {"http":"proxy_here","https":"proxy_here"} Accepts python dictionary.
config.PROXY = None
```

## Sessions Directory

```python
# Directory path/name to save and load logged in sessions/cookies. Default path is current directory. i.e. current_path/Twitter Saved Sessions
config.SESSION_DIRECTORY = "Twitter Saved Sessions"
```

## Event Loop

```python
# Fix : RuntimeError('asyncio.run() cannot be called from a running event loop') #15
# Specify if already running an event loop.
USING_EVENT_LOOP = Falses
```
