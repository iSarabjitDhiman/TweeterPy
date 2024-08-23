import bs4
import requests
import logging.config
from tweeterpy import util
from tweeterpy import config
from requests.exceptions import ProxyError, InvalidProxyURL

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class RequestClient:
    def __init__(self, session: requests.Session):
        self.session = session
        self.client_transaction = None

    def request(self, url, method=None, max_retries=None, timeout=None, skip_error_checking=False, **kwargs):
        if method is None:
            method = "GET"
        if max_retries is None:
            max_retries = config.MAX_RETRIES or 3
        if timeout is None:
            timeout = config.TIMEOUT or 30
        logger.debug(f"{locals()}")
        for retry_count, _ in enumerate(range(max_retries), start=1):
            response_text, api_limit_stats = "", {}
            try:
                response = self.session.request(
                    method, url, timeout=timeout, **kwargs)
                api_limit_stats = util.check_api_rate_limits(response) or {}
                if "json" in response.headers.get("Content-Type", ""):
                    response = response.json()
                    if api_limit_stats:
                        config._RATE_LIMIT_STATS = api_limit_stats
                        response.update({"api_rate_limit": api_limit_stats})
                    if skip_error_checking:
                        return response
                    return util.check_for_errors(response)
                soup = bs4.BeautifulSoup(response.content, "lxml")
                response_text = "\n".join(
                    [line.strip() for line in soup.text.split("\n") if line.strip()])
                response.raise_for_status()
                return soup
            except KeyboardInterrupt:
                logger.warn("Keyboard Interruption...")
                return
            except (ProxyError, InvalidProxyURL) as proxy_error:
                logger.error(f"{proxy_error}")
                if retry_count >= max_retries:
                    raise proxy_error
            except Exception as error:
                logger.debug(f"Retry No. ==> {retry_count}")
                if retry_count >= max_retries:
                    logger.exception(f"{error}\n{response_text}\n")
                    if api_limit_stats.get('exhausted'):
                        logger.error(
                            f"Rate Limit Exceeded => {api_limit_stats}")
                        raise util.RateLimitError('API Rate Limit Exceeded.')
                    raise error


if __name__ == '__main__':
    pass
