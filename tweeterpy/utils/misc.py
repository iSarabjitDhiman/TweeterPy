from typing import Any, Callable, Dict, List, Optional, Union


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


def resolve_metadata(
    metadata: Union[List[str], Dict[str, Any], None],
    resolver_func: Callable[[str], Any],
) -> Optional[Dict[str, Any]]:
    """
    Standardizes metadata (feature switches and field toggles) into a resolved dictionary.
    Flattens the output if the resolver_func returns a dictionary for a single key.
    """
    # 1. Fast-pass if already a dictionary
    if isinstance(metadata, dict):
        return metadata

    # 2. Map-and-Resolve if it's a list of names
    if isinstance(metadata, list) and len(metadata) > 0:
        resolved = {}
        for name in metadata:
            if not isinstance(name, str):
                continue

            value = resolver_func(name)

            # If the resolver returned a dict (e.g. {'name': True}), extract the value
            if isinstance(value, dict) and name in value:
                resolved[name] = value[name]
            else:
                resolved[name] = value

        return resolved

    return None


if __name__ == "__main__":
    pass
