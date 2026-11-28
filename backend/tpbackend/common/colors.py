"""colors like a game's or user's tile colors: stored as hex without #, lowercase"""

import re


def parse_color(color: str | None) -> str | None:
    """
    a color from an admin or user, as stored: hex without #, lowercase. None for empty.
    ValueError if it isn't a hex color
    """
    if color is None:
        return None
    color = color.strip().lstrip("#").lower()
    if not color:
        return None
    if not re.fullmatch("[0-9a-f]{6}", color):
        raise ValueError("must be a hex color like #1a2b3c")
    return color
