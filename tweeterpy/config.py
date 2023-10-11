# Configuration File
_DEFAULT_SESSION = None  # Used to reuse generated session. DON'T CHANGE IT
_RATE_LIMIT_STATS = None  # Used to keep a track of api limits. DON'T CHANGE IT

_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'

# Maximun number of retries for each request
MAX_RETRIES = 3

# request timeout - in seconds
TIMEOUT = 5

# Example {"http":"proxy_here","https":"proxy_here"} Accepts python dictionary.
PROXY = None

# Directory path/name to save and load logged in sessions/cookies. Default path is current directory. i.e. current_path/Twitter Saved Sessions
SESSION_DIRECTORY = "Twitter Saved Sessions"

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

# Log Configuration.
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] [Line No. %(lineno)d] %(name)s : %(funcName)s :: %(message)s'
        },
        'custom': {
            # 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            'class': 'tweeterpy.logging_util.CustomFormatter',
        }
    },
    'handlers': {
        'stream': {
            'level': LOG_LEVEL or 'INFO',
            'formatter': 'custom',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': LOG_LEVEL or 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_NAME,
            "encoding": "utf-8"
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['stream', 'file'],
            'level': LOG_LEVEL or 'DEBUG'
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['stream', 'file'],
            'level': LOG_LEVEL or 'DEBUG',
        }
    }
}

# Disable/Enable Api Update which occurs at the startup Initialization.
UPDATE_API = True

if __name__ == "__main__":
    pass
