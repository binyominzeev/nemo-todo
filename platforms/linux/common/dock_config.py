"""JSON-backed on/off switch for the docking hacks, one config file per platform."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {"dock_hack_enabled": True}


def load_dock_config(path: Path) -> dict:
    if not path.exists():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")
        except OSError:
            logger.exception("Unable to write default dock config to %s", path)
        return dict(DEFAULT_CONFIG)

    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        logger.exception("Unable to read dock config from %s", path)
        return dict(DEFAULT_CONFIG)

    if not isinstance(data, dict):
        return dict(DEFAULT_CONFIG)
    return data


def dock_hack_enabled(path: Path) -> bool:
    return bool(load_dock_config(path).get("dock_hack_enabled", True))
