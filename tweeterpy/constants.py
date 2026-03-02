import logging.config
from pathlib import Path

logger = logging.getLogger(__name__)


CURRENT_DIRECTORY = Path(__file__).resolve().parent

PACKAGE_NAME = CURRENT_DIRECTORY.name

# Filename to store api data/endpoints as a backup.
API_TMP_FILE = f"{PACKAGE_NAME}.json"

# Directory path/name to save and load logged in sessions/cookies. Default path is current directory. i.e. current_path/Twitter Saved Sessions
DEFAULT_SESSION_DIRECTORY = f"{PACKAGE_NAME} sessions"

# File name to save logs.
LOG_FILE_NAME = f"{PACKAGE_NAME}.log"

# Logging level : "DEBUG","INFO","WARNING","ERROR","CRITICAL"
# If None, "INFO" will be used for Stream/Console logs and "DEBUG" will be used for file logs.
# LOG_LEVEL = "INFO"
LOG_LEVEL = "INFO"

# Log Configuration.
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] [Line No. %(lineno)d] %(name)s : %(funcName)s :: %(message)s"
        },
        "custom": {
            # 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            "class": f"{PACKAGE_NAME}.utils.logging.CustomFormatter",
        },
    },
    "handlers": {
        "stream": {
            "level": LOG_LEVEL,
            "formatter": "custom",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": LOG_FILE_NAME,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["stream", "file"],
            "level": "DEBUG",
        },
        "__main__": {  # if __name__ == '__main__'
            "handlers": ["stream", "file"],
            "level": "DEBUG",
        },
    },
}


if __name__ == "__main__":
    pass
