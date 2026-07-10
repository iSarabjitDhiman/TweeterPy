from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from tweeterpy.core.resources import RegexPatterns, XEndpoints, XHosts
from tweeterpy.schemas.constants import APIVersion, ResponseType
from tweeterpy.schemas.types import HTMLResponse
from tweeterpy.utils.decorators import ensure_html

if TYPE_CHECKING:
    from tweeterpy.core.api import APIClient, AsyncAPIClient


class BaseXMigrationHandler:
    def __init__(self) -> None:
        pass

    @ensure_html("response")
    def get_migration_url(self, response: BeautifulSoup) -> Optional[str]:
        migration_meta = response.select_one("meta[http-equiv='refresh']")
        content = str(migration_meta) if migration_meta else str(response)
        match = RegexPatterns.MIGRATION_URL.search(content)
        return match.group(0) if match else None

    @ensure_html("response")
    def get_migration_form(self, response: BeautifulSoup) -> Optional[Dict[str, Any]]:
        migration_url = urljoin(base=XHosts.BASE, url=XEndpoints.MIGRATION)
        migration_form = response.select_one("form[name='f']") or response.select_one(
            f"form[action='{migration_url}']"
        )

        if not migration_form:
            return

        return {
            "url": migration_form.attrs.get("action", migration_url),
            "method": migration_form.attrs.get("method", "POST").upper(),
            "data": {
                input_field.get("name"): input_field.get("value")
                for input_field in migration_form.select("input")
                if input_field.get("name")
            },
        }


class XMigrationHandler(BaseXMigrationHandler):
    def __init__(self, api_client: APIClient) -> None:
        self.api_client = api_client
        super().__init__()

    def run(self, response: BeautifulSoup) -> BeautifulSoup:
        migration_url = self.get_migration_url(response=response)
        if not migration_url:
            return response

        migration_page: HTMLResponse = self.api_client.get(
            endpoint=migration_url,
            version=APIVersion.UNVERSIONED,
            response_type=ResponseType.HTML,
        )
        migration_form = self.get_migration_form(response=migration_page)
        if migration_form:
            return self.api_client.request(
                **migration_form, response_type=ResponseType.HTML
            )

        return response


class AsyncXMigrationHandler(BaseXMigrationHandler):
    def __init__(self, api_client: AsyncAPIClient) -> None:
        self.api_client = api_client
        super().__init__()

    async def run(self, response: BeautifulSoup) -> BeautifulSoup:
        migration_url = self.get_migration_url(response=response)
        if not migration_url:
            return response

        migration_page: HTMLResponse = await self.api_client.get(
            endpoint=migration_url,
            version=APIVersion.UNVERSIONED,
            response_type=ResponseType.HTML,
        )

        migration_form = self.get_migration_form(response=migration_page)
        if migration_form:
            return await self.api_client.request(
                **migration_form, response_type=ResponseType.HTML
            )

        return response


if __name__ == "__main__":
    pass
