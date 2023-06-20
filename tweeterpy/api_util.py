import re
import js2py
from .constants import Path
from .request_util import make_request


dataset_regex = re.compile(r'''exports\s*=\s*{(.*?)},''', re.VERBOSE)


class ApiUpdater:
    def __init__(self):
        try:
            # fmt: off - Turns off formatting for this block of code.
            api_endpoints_data = self._js_to_py_dict(self._get_api_file_content())
            current_api_endpoints = self._get_current_api_endpoints()
            new_api_endpoints = self._map_data(current_api_endpoints, api_endpoints_data)
            self._update_api_endpoints(new_api_endpoints)
            print("API Updated Successfully.")
        except Exception as error:
            raise Exception(f"{error}\nCouldn't Update API.")

    def _get_api_file_url(self):
        page_source = str(make_request(Path.BASE_URL))
        api_file_name = re.search(r"api:(.*?),", page_source).group(1)
        api_file_url = f"{Path.TWITTER_CDN}/api.{eval(api_file_name)}a.js"
        return api_file_url

    def _get_api_file_content(self, file_url=None):
        if file_url is None:
            file_url = self._get_api_file_url()
        return make_request(file_url)

    def _js_to_py_dict(sel, page_source):
        if isinstance(page_source, list):
            page_source = "\n".join([item for item in page_source])
        else:
            page_source = str(page_source)
        matches = []
        for match in dataset_regex.finditer(page_source):
            matches.append(match.group(0))

        api_dict = [js2py.eval_js(each_match.replace('},', ''))
                    for each_match in matches]
        return api_dict

    def _map_data(self, old_endpoints, new_endpoints):
        new_endpoints = {
            endpoint['operationName']: f"{endpoint['queryId']}/{endpoint['operationName']}" for endpoint in new_endpoints}
        mapped_data = {}
        for key, value in old_endpoints.items():
            mapped_data.update({key: new_value for new_key, new_value in new_endpoints.items()
                                if value.split("/")[-1] == new_key})
        return mapped_data

    def _get_current_api_endpoints(self):
        api_endpoints = {}
        for key, value in Path.__dict__.items():
            if not key.startswith('__'):
                api_endpoints[key] = value
        return api_endpoints

    def _update_api_endpoints(self, new_endpoints):
        for key, value in new_endpoints.items():
            setattr(Path, key, value)


if __name__ == "__main__":
    pass
