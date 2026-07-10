from __future__ import annotations

from typing import Dict, Optional

from tweeterpy.core.resources import RegexPatterns, XHosts
from tweeterpy.schemas.base import TweeterPySchema


class ScriptBundle(TweeterPySchema):
    """Represents a compiled, code-split JavaScript chunk from X's frontend."""

    id: Optional[int] = None
    name: str
    hash: str

    @property
    def filename(self) -> str:
        """Returns the cache-busted filename (e.g., 'loader.SideNav.21bc47da.js')."""
        # X appends an 'a' suffix right before the .js extension for client runtimes
        return f"{self.name}.{self.hash}a.js"

    @property
    def url(self) -> str:
        """The absolute path to download this asset from the X static CDN."""
        return f"{XHosts.CDN}/{self.filename}"

    @staticmethod
    def from_url(url: str) -> ScriptBundle:
        """Extracts and initializes a ScriptBundle instance directly from an absolute asset URL."""
        bundle_match = RegexPatterns.JS_BUNDLES.search(url)
        if not bundle_match:
            raise ValueError(
                f"Failed to parse X script bundle metadata from URL: '{url}'"
            )

        return ScriptBundle(
            id=None,
            name=bundle_match.group("bundle_name"),
            hash=bundle_match.group("bundle_hash"),
        )


class BundleManifest(TweeterPySchema):
    """Container for parsed runtime manifest definitions."""

    bundles: Dict[str, ScriptBundle]


if __name__ == "__main__":
    pass
