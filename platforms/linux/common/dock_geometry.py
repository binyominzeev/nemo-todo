"""Pure geometry helpers shared by the Dolphin and Nemo docking hacks."""

from typing import NamedTuple


class Geometry(NamedTuple):
    x: int
    y: int
    width: int
    height: int


def compute_dock_geometry(target: Geometry, panel_width: int, screen_width: int) -> Geometry:
    """Place the panel to the right of ``target``, flipping to the left if it would overflow."""
    x = target.x + target.width
    if x + panel_width > screen_width:
        x = target.x - panel_width
    return Geometry(x=x, y=target.y, width=panel_width, height=target.height)
