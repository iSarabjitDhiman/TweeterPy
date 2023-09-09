import requests
import bs4
import logging.config
from . import util
from . import config

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def make_request(url, session=None, method=None, max_retries=None, timeout=None, skip_error_checking=False, **kwargs):
    if method is None:
        method = "GET"
    if max_retries is None:
        max_retries = config.MAX_RETRIES or 3
    if session is None:
        session = config._DEFAULT_SESSION or requests.Session()
    if timeout is None:
        timeout = config.TIMEOUT or 30
    logger.debug(f"{locals()}")
    for retry_count, _ in enumerate(range(max_retries), start=1):
        response_text, api_limit_stats = "", {}
        try:
            response = session.request(method, url, timeout=timeout, **kwargs)
            api_limit_stats = util.check_api_rate_limits(response) or {}
            if api_limit_stats:
                config._RATE_LIMIT_STATS = api_limit_stats
            soup = bs4.BeautifulSoup(response.content, "lxml")
            if "json" in response.headers["Content-Type"]:
                if skip_error_checking:
                    return response.json()
                return util.check_for_errors(response.json())
            response_text = "\n".join(
                [line.strip() for line in soup.text.split("\n") if line.strip()])
            response.raise_for_status()
            return soup
        except KeyboardInterrupt:
            logger.warn("Keyboard Interruption...")
            return
        except Exception as error:
            logger.debug(f"Retry No. ==> {retry_count}")
            if retry_count >= max_retries:
                logger.exception(f"{error}\n{response_text}\n")
                if api_limit_stats.get('rate_limit_exhausted'):
                    logger.error(f"Rate Limit Exceeded => {api_limit_stats}")
                raise error


if __name__ == '__main__':
    pass
