import httpx
import asyncio
import bs4
from . import util
from . import config


def make_request(url=None, method=None, params=None, request_payload=None, session=None, max_retries=None, timeout=None, **kwargs):
    # fmt: off - Turns off formatting for this block of code. Just for the readability purpose.
    def make_regular_request(request_payload):
        return validate_response(session.request(**request_payload))

    async def make_async_request(**kwargs):
        response = await session.request(**kwargs)
        return validate_response(response)

    async def make_concurrent_requests(request_payload):
        if isinstance(request_payload,list):
            tasks_list = [asyncio.create_task(make_async_request(**request)) for request in request_payload]
        else:
            query_params = request_payload.pop("params")
            tasks_list = [asyncio.create_task(make_async_request(params=query,**request_payload)) for query in  query_params]
        return await asyncio.gather(*tasks_list, return_exceptions=True)

    method = method or "GET"
    timeout = timeout or config.TIMEOUT or 10
    proxies = config.PROXY or None
    ssl_verify = False if proxies else True
    concurrent_requests = False
    session = session or config._DEFAULT_SESSION or httpx.Client(follow_redirects=True, timeout=timeout, proxies=proxies, verify=ssl_verify)
    if request_payload:
        concurrent_requests = True if isinstance(request_payload,list) or (isinstance(request_payload,dict) and isinstance(request_payload.get("params"),list)) else False
        if concurrent_requests:
            connection_limits = httpx.Limits(max_connections=100, max_keepalive_connections=10, keepalive_expiry=5)
            headers,cookies = session.headers,session.cookies
            session = httpx.AsyncClient(limits=connection_limits,headers=headers,cookies=cookies,follow_redirects=True,timeout=timeout,proxies=proxies,verify=ssl_verify)
            return asyncio.run(make_concurrent_requests(request_payload))
    else:
        request_payload = {"method":method,"url":url,"params":params} | kwargs
    return make_regular_request(request_payload)


def validate_response(response):
    try:
        response_text = ""
        api_limit_stats = util.check_api_rate_limits(response)
        soup = bs4.BeautifulSoup(response.content, "lxml")
        if "json" in response.headers["Content-Type"]:
            return util.check_for_errors(response.json())
        response_text = "\n".join([line.strip() for line in soup.text.split("\n") if line.strip()])
        response.raise_for_status()
        return soup
    except Exception as error:
        # print(f"{error}\n\n{response_text}\n")
        if api_limit_stats and api_limit_stats.get('rate_limit_exhausted'):
            print(f"\033[91m Rate Limit Exceeded:\033[0m {api_limit_stats}")
        raise error


if __name__ == '__main__':
    pass
