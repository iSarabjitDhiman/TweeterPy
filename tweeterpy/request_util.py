import requests
import bs4
from . import util
from . import config


def make_request(url, session=None, method=None, max_retries=None, timeout=None, **kwargs):
    if method is None:
        method = "GET"
    if max_retries is None:
        max_retries = config.MAX_RETRIES or 3
    if session is None:
        session = config._DEFAULT_SESSION or requests.Session()
    if timeout is None:
        timeout = config.TIMEOUT or 30
    for retry_count, _ in enumerate(range(max_retries), start=1):
        try:
            response_text = ""
            response = session.request(method, url, timeout=timeout, **kwargs)
            api_limit_stats = util.check_api_rate_limits(response)
            soup = bs4.BeautifulSoup(response.content, "lxml")
            if "json" in response.headers["Content-Type"]:
                return util.check_for_errors(response.json())
            response_text = "\n".join(
                [line.strip() for line in soup.text.split("\n") if line.strip()])
            response.raise_for_status()
            return soup
        except KeyboardInterrupt:
            print("Keyboard Interruption...")
            return
        except Exception as error:
            print(f"Retry No. ==> {retry_count}", end="\r")
            if retry_count >= max_retries:
                print(f"{error}\n\n{response_text}\n")
                if api_limit_stats.get('rate_limit_exhausted'):
                    print(
                        f"\033[91m Rate Limit Exceeded:\033[0m {api_limit_stats}")
                raise error


if __name__ == '__main__':
    pass
