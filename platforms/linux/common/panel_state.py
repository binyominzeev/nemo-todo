"""JSON-backed persistence for the last manually-resized panel width."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_panel_width(path: Path, default: int) -> int:
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        logger.exception("Unable to read panel width from %s", path)
        return default
    width = data.get("panel_width") if isinstance(data, dict) else None
    return width if isinstance(width, int) and width > 0 else default


def save_panel_width(path: Path, width: int) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"panel_width": width}, indent=2) + "\n")
    except OSError:
        logger.exception("Unable to write panel width to %s", path)
