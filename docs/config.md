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

## Retries Limit

```python
# Maximun number of retries for each request
config.MAX_RETRIES = 3
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

## Logs

```python
# File name to save logs.
LOG_FILE_NAME = "tweeterpy.log"

# Logging level : "DEBUG","INFO","WARNING","ERROR","CRITICAL"
# If None, "INFO" will be used for Stream/Console logs and "DEBUG" will be used for file logs.
# LOG_LEVEL = "INFO"
LOG_LEVEL = None

# Disable logs for imported modules/libraries only.
DISABLE_EXTERNAL_LOGS = False

# Disable logs completely. (It sets logging level to "ERROR".)
DISABLE_LOGS = False

# Log Configuration. Set Custom Log configuration in dict format.
LOGGING_CONFIG = {}
```

## API Updates

```python
# Disable/Enable Api Update which occurs at the startup Initialization.
UPDATE_API = True
```
