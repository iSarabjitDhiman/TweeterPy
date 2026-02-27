from typing import Any, Dict

from tweeterpy.core.resources import XUrls


class TweeterPyConfig:
    BEARER_TOKEN = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"

    @classmethod
    def headers(cls) -> Dict[str, Any]:
        return {
            "authority": XUrls.DOMAIN,
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "referer": XUrls.BASE,
            "user-agent": cls.USER_AGENT,
        }


if __name__ == "__main__":
    pass
