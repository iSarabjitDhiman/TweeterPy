import re
import json
import js2py
from .constants import Path, FeatureSwitch
from .request_util import make_request


dataset_regex = re.compile(r'''exports\s*=\s*{(.*?)},''', re.VERBOSE)
api_file_regex = re.compile(r'''api:(.*?),''', re.VERBOSE)
feature_switch_regex = re.compile(r'''.featureSwitch.:(.*?)}},''', re.VERBOSE)


class ApiUpdater:
    """ 
        Twitter updates its API quite frequently. Therefore, ApiUpdater checks for the latest updates and modifies the api_endpoints, feature_switches, path etc in constants.py
    """

    def __init__(self):
        try:
            # fmt: off - Turns off formatting for this block of code.
            page_source = self._get_home_page_source()
            api_file_url = self._get_api_file_url(page_source)
            feature_switches = self._get_feature_switches(page_source)
            api_endpoints_data = self._js_to_py_dict(self._get_api_file_content(api_file_url))
            current_api_endpoints = self._get_current_api_endpoints()
            new_api_endpoints = self._map_data(current_api_endpoints, api_endpoints_data)
            self._update_api_endpoints(new_api_endpoints)
            self._update_feature_switches(feature_switches)
            print("API Updated Successfully.")
        except Exception as error:
            raise Exception(f"{error}\nCouldn't Update API.")

    def _get_home_page_source(self):
        return str(make_request(Path.BASE_URL))

    def _get_api_file_url(self,page_source=None):
        if page_source is None:
            page_source = self._get_home_page_source
        api_file_name = re.search(api_file_regex, page_source).group(1)
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

        dict_data = [js2py.eval_js(each_match.replace('},', ''))
                    for each_match in matches]
        return dict_data

    def _map_data(self, old_endpoints, new_endpoints):
        FeatureSwitch.api_endpoints = {f"{endpoint['queryId']}/{endpoint['operationName']}" : endpoint for endpoint in new_endpoints}
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

    def _get_feature_switches(self,page_source=None):
        if page_source is None:
            self._get_home_page_source()
        feature_switch_data = re.search(feature_switch_regex,str(page_source)).group(0)
        return json.loads("{"+feature_switch_data.rstrip(',')+"}}")

    def _update_feature_switches(self,feature_switches=None):
        if feature_switches is None:
            feature_switches = self._get_feature_switches()
        FeatureSwitch.all_feature_switches = feature_switches['featureSwitch']['defaultConfig']

if __name__ == "__main__":
    pass
