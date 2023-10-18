import re
import json
import demjson3
import os
import tempfile
import logging.config
from .constants import Path, FeatureSwitch, API_TMP_FILE
from .request_util import make_request
from . import config

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

dataset_regex = re.compile(r'''exports\s*=\s*{(.*?)},''', re.VERBOSE)
api_file_regex = re.compile(r'''api:(.*?),''', re.VERBOSE)
main_file_regex = re.compile(r'''main(.?)(\w*).?js''', re.VERBOSE)
feature_switch_regex = re.compile(r'''.featureSwitch.:(.*?)}},''', re.VERBOSE)
# logging.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s [%(levelname)s] %(module)s : %(funcName)s : %(lineno)d ::: %(message)s')


class ApiUpdater:
    """
        Twitter updates its API quite frequently. Therefore, ApiUpdater checks for the latest updates and modifies the api_endpoints, feature_switches, path etc in constants.py
    """

    def __init__(self, update_api=True):
        try:
            logger.debug('Updating API...')
            # fmt: off - Turns off formatting for this block of code.
            try:
                if not update_api:
                    raise Exception("Skipping API Updates.")
                api_files_data = []
                page_source = self._get_home_page_source()
                api_file_url = self._get_api_file_url(page_source)
                main_file_url = self._get_main_file_url(page_source)
                feature_switches = self._get_feature_switches(page_source)
                if api_file_url:
                    api_files_data.append(self._get_api_file_content(api_file_url))
                if main_file_url:
                    api_files_data.append(self._get_main_file_content(main_file_url))
                if not api_files_data:
                    raise Exception("Couldn't get the API files content.")
                api_endpoints_data = self._js_to_py_dict(api_files_data)
                self._save_api_data(feature_switches,api_endpoints_data)
            except Exception as error:
                logger.warn(f"{error} Couldn't get the latest API data.")
                logger.debug("Trying to restore API data from the backup file.")
                feature_switches, api_endpoints_data = self._load_api_data()
            current_api_endpoints = self._get_current_api_endpoints()
            new_api_endpoints = self._map_data(current_api_endpoints, api_endpoints_data)
            self._update_api_endpoints(new_api_endpoints)
            self._update_feature_switches(feature_switches)
            logger.info("API Updated Successfully.")
        except Exception as error:
            logger.exception(f"API Couldn't be Updated.\n{error}")
            raise
            # fmt: on 

    def _get_home_page_source(self):
        return str(make_request(Path.BASE_URL))

    def _get_api_file_url(self, page_source=None):
        if page_source is None:
            page_source = self._get_home_page_source
        try:
            api_file_name = re.search(api_file_regex, page_source).group(1)
            api_file_url = f"{Path.TWITTER_CDN}/api.{eval(api_file_name)}a.js"
            logger.debug(f"API Url => {api_file_url}")
        except Exception as error:
            logger.exception(f"Couldn't get the API file Url.\n{error}")
            return None
        return api_file_url

    def _get_main_file_url(self, page_source=None):
        if page_source is None:
            page_source = self._get_home_page_source
        try:
            main_file_name = re.search(main_file_regex, page_source).group(0)
            main_file_url = f"{Path.TWITTER_CDN}/{main_file_name}"
            logger.debug(f"Main File Url => {main_file_url}")
        except Exception as error:
            logger.exception(f"Couldn't get the main file Url.\n{error}")
            return None
        return main_file_url

    def _get_api_file_content(self, file_url=None):
        if file_url is None:
            file_url = self._get_api_file_url()
        return str(make_request(file_url))

    def _get_main_file_content(self, file_url=None):
        if file_url is None:
            file_url = self._get_main_file_url()
        return str(make_request(file_url))

    def _js_to_py_dict(sel, page_source):
        if isinstance(page_source, list):
            page_source = "\n".join([str(item) for item in page_source])
        else:
            page_source = str(page_source)
        matches = []
        for match in dataset_regex.finditer(page_source):
            matches.append(match.group(1))

        dict_data = [demjson3.decode("{" + each_match)
                     for each_match in matches if "function" not in each_match]
        return dict_data

    def _map_data(self, old_endpoints, new_endpoints):
        FeatureSwitch.api_endpoints = {
            f"{endpoint['queryId']}/{endpoint['operationName']}": endpoint for endpoint in new_endpoints}
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

    def _get_feature_switches(self, page_source=None):
        if page_source is None:
            self._get_home_page_source()
        feature_switch_data = re.search(
            feature_switch_regex, str(page_source)).group(0)
        return json.loads("{"+feature_switch_data.rstrip(',')+"}}")

    def _update_feature_switches(self, feature_switches=None):
        if feature_switches is None:
            feature_switches = self._get_feature_switches()
        FeatureSwitch.all_feature_switches = feature_switches['featureSwitch']['defaultConfig']

    def _save_api_data(self, feature_switches=None, endpoints_data=None, filename=None):
        try:
            if not feature_switches or not endpoints_data:
                logger.exception(
                    "feature_switches or endpoints_data is invalid.")
                raise TypeError("Invalid API Data.")
            if filename is None:
                filename = os.path.join(tempfile.gettempdir(), API_TMP_FILE)
            api_data = {"feature_switches": feature_switches,
                        "endpoints_data": endpoints_data}
            logger.debug("Saving API data to the temp file.")
            with open(filename, "w+") as backup_file:
                json.dump(api_data, backup_file)
            logger.debug("API data saved successfully.")
        except Exception as error:
            logger.warn(f"Couldn't save API data.\n{error}")
        return

    def _load_api_data(self, filename=None):
        try:
            if filename is None:
                filename = os.path.join(tempfile.gettempdir(), API_TMP_FILE)
            if not os.path.exists(filename):
                logger.warn("Couldn't find the API backup file.")
                raise
            logger.debug("Restoring API data from the backup file.")
            with open(filename, "r+") as backup_file:
                api_data = json.load(backup_file)
            feature_switches = api_data.get("feature_switches")
            endpoints = api_data.get("endpoints_data")
            logger.debug("API data restored successfully.")
        except Exception as error:
            logger.warn(
                f"Couldn't restore API data from the backup file.\n{error}")
            raise
        return feature_switches, endpoints


if __name__ == "__main__":
    pass
