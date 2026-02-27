from typing import Any


def is_json_response(response: Any) -> bool:
    """
    Checks if an HTTP response contains JSON content by inspecting headers.
    Safe for use with httpx, requests, and curl_cffi.
    """
    if response is None:
        return False

    # Safely get headers (handles missing 'headers' attribute)
    headers = getattr(response, "headers", {})

    # Check for 'Content-Type' or 'content-type' (case-insensitive fetch)
    content_type = str(
        headers.get("Content-Type", headers.get("content-type", ""))
    ).lower()

    return "application/json" in content_type or "json" in content_type


if __name__ == "__main__":
    pass
