from typing import Any, Awaitable, Dict, Optional, Union

from bs4 import BeautifulSoup

from tweeterpy.core.abstractions import TweeterPySession
from tweeterpy.core.resources import RegexPatterns, XUrls
from tweeterpy.utils.decorators import ensure_html


class XMigrationHandler:
    def __init__(self, session: TweeterPySession) -> None:
        self.session = session

    @ensure_html("response")
    def get_migration_url(self, response: BeautifulSoup) -> Optional[str]:
        migration_meta = response.select_one("meta[http-equiv='refresh']")
        content = str(migration_meta) if migration_meta else str(response)
        match = RegexPatterns.MIGRATION_URL.search(content)
        return match.group(0) if match else None

    @ensure_html("response")
    def get_migration_form(self, response: BeautifulSoup) -> Optional[Dict[str, Any]]:
        migration_form = response.select_one("form[name='f']") or response.select_one(
            f"form[action='{XUrls.X_MIGRATION}']"
        )

        if not migration_form:
            return

        return {
            "url": migration_form.attrs.get("action", XUrls.X_MIGRATION),
            "method": migration_form.attrs.get("method", "POST").upper(),
            "data": {
                input_field.get("name"): input_field.get("value")
                for input_field in migration_form.select("input")
                if input_field.get("name")
            },
        }

    def run(self, response: BeautifulSoup):
        migration_url = self.get_migration_url(response=response)
        if not migration_url:
            return response

        migration_page = self.session.request_html(method="GET", url=migration_url)
        migration_form = self.get_migration_form(response=migration_page)
        if migration_form:
            return self.session.request(**migration_form)

        return response

    async def run_async(self, response: BeautifulSoup):
        migration_url = self.get_migration_url(response=response)
        if not migration_url:
            return response

        migration_page = await self.session.request_html(
            method="GET", url=migration_url
        )
        migration_form = self.get_migration_form(response=migration_page)
        if migration_form:
            return await self.session.request(**migration_form)

        return response

    def migrate(
        self, response: BeautifulSoup
    ) -> Union[BeautifulSoup, Awaitable[BeautifulSoup]]:
        if self.session.is_async:
            return self.run_async(response=response)

        return self.run(response=response)


if __name__ == "__main__":
    pass
