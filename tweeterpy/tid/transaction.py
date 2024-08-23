import re
import bs4
import math
import time
import random
import base64
import hashlib
import requests
from functools import reduce
from typing import Union, List
from tweeterpy.constants import Path
from tweeterpy.tid.cubic_curve import Cubic
from tweeterpy.tid.interpolate import interpolate
from tweeterpy.tid.rotation import convert_rotation_to_matrix
from tweeterpy.tid.util import float_to_hex, is_odd, base64_encode

ON_DEMAND_FILE_REGEX = re.compile(
    r"""['|\"]{1}ondemand\.s['|\"]{1}:\s*['|\"]{1}([\w]*)['|\"]{1}""", flags=(re.VERBOSE | re.MULTILINE))
INDICES_REGEX = re.compile(
    r"""(\(\w{1}\[(\d{1,2})\],\s*16\))+""", flags=(re.VERBOSE | re.MULTILINE))


class ClientTransaction:
    DEFAULT_KEYWORD = "obfiowerehiring"
    ADDITIONAL_RANDOM_NUMBER = 3
    DEFAULT_ROW_INDEX = None
    DEFAULT_KEY_BYTES_INDICES = None

    def __init__(self, home_page_response: Union[bs4.BeautifulSoup, requests.models.Response]):
        self.home_page_response = self.validate_response(home_page_response)
        self.DEFAULT_ROW_INDEX, self.DEFAULT_KEY_BYTES_INDICES = self.get_indices(
            self.home_page_response)
        self.key = self.get_key(response=self.home_page_response)
        self.key_bytes = self.get_key_bytes(key=self.key)
        self.animation_key = self.get_animation_key(
            key_bytes=self.key_bytes, response=self.home_page_response)

    def get_indices(self, home_page_response=None):
        key_byte_indices = []
        response = self.validate_response(
            home_page_response) or self.home_page_response
        on_demand_file = ON_DEMAND_FILE_REGEX.search(str(response))
        if on_demand_file:
            on_demand_file_url = f"{Path.TWITTER_CDN}/ondemand.s.{on_demand_file.group(1)}a.js"
            on_demand_file_response = requests.get(on_demand_file_url)
            key_byte_indices_match = INDICES_REGEX.finditer(
                str(on_demand_file_response.text))
            for item in key_byte_indices_match:
                key_byte_indices.append(item.group(2))
        if not key_byte_indices:
            raise Exception("Couldn't get animation key indices")
        key_byte_indices = list(map(int, key_byte_indices))
        return key_byte_indices[0], key_byte_indices[1:]

    def validate_response(self, response: Union[bs4.BeautifulSoup, requests.models.Response]):
        if not isinstance(response, (bs4.BeautifulSoup, requests.models.Response)):
            raise Exception("invalid response")
        return response if isinstance(response, bs4.BeautifulSoup) else bs4.BeautifulSoup(response.content, 'lxml')

    def get_key(self, response=None):
        response = self.validate_response(response) or self.home_page_response
        # <meta name="twitter-site-verification" content="mentU...+1yPz..../IcNS+......./RaF...R+b"/>
        element = response.select_one("[name='twitter-site-verification']")
        if not element:
            raise Exception("Couldn't get twitter site verification code")
        return element.get("content")

    def get_key_bytes(self, key: str):
        return list(base64.b64decode(bytes(key, 'utf-8')))

    def get_frames(self, response=None):
        # loading-x-anim-0...loading-x-anim-3
        response = self.validate_response(response) or self.home_page_response
        return response.select("[id^='loading-x-anim']")

    def get_2d_array(self, key_bytes: List[Union[float, int]], response, frames: bs4.ResultSet = None):
        if not frames:
            frames = self.get_frames(response)
        return [[int(x) for x in re.sub(r"[^\d]+", " ", item).strip().split()] for item in list(list(frames[key_bytes[5] % 4].children)[0].children)[1].get("d")[9:].split("C")]

    def solve(self, value, min_val, max_val, rounding: bool):
        result = value * (max_val-min_val) / 255 + min_val
        return math.floor(result) if rounding else round(result, 2)

    def animate(self, frames, target_time):
        from_color = [float(item) for item in [*frames[:3], 1]]
        to_color = [float(item) for item in [*frames[3:6], 1]]
        from_rotation = [0.0]
        to_rotation = [self.solve(float(frames[6]), 60.0, 360.0, True)]
        frames = frames[7:]
        curves = [self.solve(float(item), is_odd(counter), 1.0, False)
                  for counter, item in enumerate(frames)]
        cubic = Cubic(curves)
        val = cubic.get_value(target_time)
        color = interpolate(from_color, to_color, val)
        color = [value if value > 0 else 0 for value in color]
        rotation = interpolate(from_rotation, to_rotation, val)
        matrix = convert_rotation_to_matrix(rotation[0])
        str_arr = [format(round(value), 'x') for value in color[:-1]]
        for value in matrix:
            rounded = round(value, 2)
            if rounded < 0:
                rounded = -rounded
            hex_value = float_to_hex(rounded)
            str_arr.append(f"0{hex_value}".lower() if hex_value.startswith(
                ".") else hex_value if hex_value else '0')
        str_arr.extend(["0", "0"])
        animation_key = re.sub(r"[.-]", "", "".join(str_arr))
        return animation_key

    def get_animation_key(self, key_bytes, response):
        total_time = 4096
        row_index = key_bytes[self.DEFAULT_ROW_INDEX] % 16
        frame_time = reduce(lambda num1, num2: num1*num2,
                            [key_bytes[index] % 16 for index in self.DEFAULT_KEY_BYTES_INDICES])
        arr = self.get_2d_array(key_bytes, response)
        frame_row = arr[row_index]

        target_time = float(frame_time) / total_time
        animation_key = self.animate(frame_row, target_time)
        return animation_key

    def generate_transaction_id(self, method: str, path: str, response=None, key=None, animation_key=None, time_now=None):
        "X-Client-Transaction-Id"
        try:
            time_now = time_now or math.floor(
                (time.time() * 1000 - 1682924400 * 1000) / 1000)
            time_now_bytes = [(time_now >> (i * 8)) & 0xFF for i in range(4)]
            key = key or self.key or self.get_key(response)
            key_bytes = self.get_key_bytes(key)
            animation_key = animation_key or self.animation_key or self.get_animation_key(
                key_bytes, response)
            hash_val = hashlib.sha256(
                f"{method}!{path}!{time_now}{self.DEFAULT_KEYWORD}{animation_key}".encode()).digest()
            hash_bytes = list(hash_val)
            random_num = random.randint(0, 255)
            bytes_arr = [*key_bytes, *time_now_bytes, *
                         hash_bytes[:16], self.ADDITIONAL_RANDOM_NUMBER]
            out = bytearray(
                [random_num, *[item ^ random_num for item in bytes_arr]])
            return base64_encode(out).strip("=")
        except Exception as error:
            raise Exception(f"Couldn't generate transaction ID.\n{error}")


if __name__ == "__main__":
    pass
