import os
from urllib.parse import unquote, urlparse


def normalize_folder_path(value: str) -> str:
    if not value:
        raise ValueError("Folder path is required")

    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme != "file":
        raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")

    raw_path = unquote(parsed.path) if parsed.scheme == "file" else value
    if not raw_path:
        raise ValueError("Folder path is empty")

    expanded = os.path.expanduser(raw_path)
    normalized = os.path.realpath(os.path.normpath(os.path.abspath(expanded)))
    return normalized
