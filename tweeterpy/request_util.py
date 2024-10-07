import bs4
import time
import requests
import logging.config
from tweeterpy import util
from tweeterpy import config
from urllib.parse import urlparse
from tweeterpy.tid import ClientTransaction
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
        tid = None
        logger.debug(f"{locals()}")
        headers = kwargs.pop("headers", {})
        if isinstance(self.client_transaction, ClientTransaction):
            tid = self.client_transaction.generate_transaction_id(
                method=method, path=urlparse(url).path)
            headers["X-Client-Transaction-Id"] = tid
        for retry_count, _ in enumerate(range(max_retries), start=1):
            response_text, api_limit_stats = "", {}
            try:
                response = self.session.request(
                    method, url, headers=headers, timeout=timeout, **kwargs)
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
            except requests.exceptions.HTTPError as http_err:
                if http_err.response.status_code == 429:
                    print(f"Response: {http_err.response.text}")
                    # usually the rate limit is 7-8 mins and doesn't exceed 10
                    # it is possible that the response tells us how long are we
                    # rate limited but extracting it is error prone and may break
                    # if the response is reformatted from the their end.
                    # This should work for most people yet in future we may allow
                    # the user to configure the timeout explicitly or supply a
                    # callback method to extract timeout from response.
                    print("Cooldown for 10 Minutes")
                    print(f"going to sleep at {time.strftime("%H:%M:%S", time.localtime())}")
                    time.sleep(600)
                    print("Awake. Retrying...")
                    continue
                else:
                    print(f"HTTP error occurred: {http_err}")
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
                    # these retries dont help us as we need to wait for some time
                    # and all attempts are exhaused before the rate limit expires
                    if api_limit_stats.get('rate_limit_exhausted'):
                        logger.error(
                            f"Rate Limit Exceeded => {api_limit_stats}")
                        raise util.RateLimitError('API Rate Limit Exceeded.')
                    raise error


if __name__ == '__main__':
    pass
