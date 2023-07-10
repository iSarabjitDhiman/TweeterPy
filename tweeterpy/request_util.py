import httpx
import asyncio
import bs4
import json
from . import util
from . import config
from functools import reduce


def make_request(url=None, method=None, params=None, request_payload=None, session=None, timeout=None, **kwargs):
    # fmt: off - Turns off formatting for this block of code. Just for the readability purpose.
    def make_regular_request(request_payload):
        return validate_response(session.request(**request_payload))

    async def make_async_request(request_payload):
        pagination_data = request_payload.pop("pagination_data",None)
        if not pagination_data:
            response = await session.request(**request_payload)
            return validate_response(response)
        return await _handle_pagination(request_payload=request_payload,session=session,**pagination_data)

    async def make_concurrent_requests(request_payload):
        if isinstance(request_payload,list):
            tasks_list = [asyncio.create_task(make_async_request(payload)) for payload in request_payload]
        else:
            query_params = request_payload.pop("params",None)
            query_params = [query_params] if not isinstance(query_params,list) else query_params
            if not query_params:
                return 
            tasks_list = [asyncio.create_task(make_async_request({"params":query} | request_payload)) for query in query_params]
        return await asyncio.gather(*tasks_list, return_exceptions=True)

    method = method or "GET"
    timeout = timeout or config.TIMEOUT or 10
    proxies = config.PROXY or None
    ssl_verify = False if proxies else True
    concurrent_requests = False
    session = session or config._DEFAULT_SESSION or httpx.Client(follow_redirects=True, timeout=timeout, proxies=proxies, verify=ssl_verify)
    if request_payload:
        concurrent_requests = True if request_payload.get("pagination_data") or isinstance(request_payload,list) or (isinstance(request_payload,dict) and isinstance(request_payload.get("params"),list)) else False
        if concurrent_requests:
            connection_limits = httpx.Limits(max_connections=100, max_keepalive_connections=10, keepalive_expiry=5)
            headers,cookies = session.headers,session.cookies
            session = httpx.AsyncClient(limits=connection_limits,headers=headers,cookies=cookies,follow_redirects=True,timeout=timeout,proxies=proxies,verify=ssl_verify)
            return asyncio.run(make_concurrent_requests(request_payload))
    else:
        request_payload = {"method":method,"url":url,"params":params} | kwargs
    return make_regular_request(request_payload)

async def _handle_pagination(url=None, query_params=None, request_payload=None,session=None,end_cursor=None,total=None,**kwargs):
        # fmt: off  - Turns off formatting for this block of code. Just for the readability purpose.
    def filter_data(response):
        filtered_data = []
        for each_entry in response:
            if each_entry['entryId'].startswith('cursor-top') or each_entry['entryId'].startswith('cursor-bottom'):
                continue
            filtered_data.append(each_entry)
            if total is not None and (len(data_container['data']) + len(filtered_data)) >= total:
                return filtered_data
        return filtered_data

    data_container = {"data": [],"cursor_endpoint": None, "has_next_page": True}
    request_payload = request_payload or {"url": url, "params": query_params} | kwargs
    while data_container["has_next_page"]:
        try:
            if end_cursor:
                varaibles = json.loads(request_payload["params"]['variables'])
                varaibles['cursor'] = end_cursor
                request_payload["params"]['variables'] = json.dumps(varaibles)
            response = await session.request(**request_payload)
            response = validate_response(response)
            data = util.find_nested_key(response,"entries")
            data = data[0] if data else None
            if not data:
                return response
            top_cursor = [
                entry for entry in data if entry['entryId'].startswith('cursor-top')]
            if top_cursor:
                top_cursor = reduce(dict.get, ('content','value'),top_cursor[0]) or reduce(dict.get, ('content','itemContent','value'),end_cursor[0])
            end_cursor = [
                entry for entry in data if entry['entryId'].startswith('cursor-bottom')]
            if end_cursor:
                end_cursor = reduce(dict.get, ('content','value'),end_cursor[0]) or reduce(dict.get, ('content','itemContent','value'),end_cursor[0])
            data_container['data'].extend(filter_data(data))

            print(len(data_container['data']), end="\r")

            if end_cursor:
                data_container['cursor_endpoint'] = end_cursor

            if ((top_cursor and end_cursor) and len(data) == 2) or ((top_cursor or end_cursor) and len(data) == 1) or (not end_cursor):
                data_container["has_next_page"] = False

            if not data_container["has_next_page"] or (total is not None and len(data_container['data']) >= total):
                return data_container
        # fmt: on 
        except ConnectionError as error:
            print(error)
            continue

        except Exception as error:
            print(error)
            return data_container


def validate_response(response):
    try:
        response_text = ""
        api_limit_stats = util.check_api_rate_limits(response)
        soup = bs4.BeautifulSoup(response.content, "lxml")
        if "json" in response.headers["Content-Type"]:
            return util.check_for_errors(response.json())
        response_text = "\n".join(
            [line.strip() for line in soup.text.split("\n") if line.strip()])
        response.raise_for_status()
        return soup
    except Exception as error:
        # print(f"{error}\n\n{response_text}\n")
        if api_limit_stats and api_limit_stats.get('rate_limit_exhausted'):
            print(f"\033[91m Rate Limit Exceeded:\033[0m {api_limit_stats}")
        raise error


if __name__ == '__main__':
    pass
