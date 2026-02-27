import datetime
import logging.config
import os
import tempfile
import time

from tweeterpy.constants import API_TMP_FILE, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class RateLimitError(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "Rate limit exceeded."
        super().__init__(message)


def check_api_rate_limits(response):
    # fmt:off - Code fomatting turned off
    try:
        current_time = time.time()
        api_requests_limit = response.headers.get("x-rate-limit-limit")
        remaining_api_requests = response.headers.get("x-rate-limit-remaining")
        limit_reset_timestamp = response.headers.get("x-rate-limit-reset")
        if api_requests_limit is None:
            return None
        api_requests_limit, remaining_api_requests, limit_reset_timestamp = map(
            int, [api_requests_limit, remaining_api_requests, limit_reset_timestamp]
        )
        limit_exhausted = True if remaining_api_requests == 0 else False
        remaining_time_datetime_object = datetime.timedelta(
            seconds=limit_reset_timestamp - current_time
        )
        # convert to human readable format
        remaining_time = str(remaining_time_datetime_object).split(":")
        remaining_time = f"{remaining_time[0]} Hours, {remaining_time[1]} Minutes, {float(remaining_time[2]):.2f} Seconds"
        # fmt:on
        api_limit_stats = {
            "total_limit": api_requests_limit,
            "remaining_requests_count": remaining_api_requests,
            "resets_after": remaining_time,
            "reset_after_datetime_object": remaining_time_datetime_object,
            "rate_limit_exhausted": limit_exhausted,
        }
        logger.debug(api_limit_stats)
        return api_limit_stats
    except:
        return None


def update_required():
    try:
        current_time = datetime.datetime.now()
        api_backup_file = os.path.join(tempfile.gettempdir(), API_TMP_FILE)
        last_modified = os.path.getmtime(api_backup_file)
        yesterday_time = current_time - datetime.timedelta(hours=24)
        one_day_elapsed = yesterday_time.timestamp() > last_modified
        if one_day_elapsed:
            return True
        return False
    except Exception as error:
        logger.warn(error)
        return True


if __name__ == "__main__":
    pass
