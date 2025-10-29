import os
import re
from typing import Dict, Tuple, Optional

NONSTANDARD_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nonstandard.md')


def parse_nonstandard_file(path: Optional[str] = None) -> Tuple[Dict[str, str], Dict[str, Tuple[float, float]]]:
    """Parse nonstandard.md into alias->address and alias->(lat, lon) maps."""
    if path is None:
        path = NONSTANDARD_FILE

    alias_to_address: Dict[str, str] = {}
    alias_to_coords: Dict[str, Tuple[float, float]] = {}

    if not os.path.exists(path):
        return alias_to_address, alias_to_coords

    with open(path, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            if ':' not in line:
                continue
            alias, rhs = line.split(':', 1)
            alias = alias.strip()
            rhs = rhs.strip()

            m = re.match(r'^(-?\d+(?:\.\d+)?)[ ,]+(-?\d+(?:\.\d+)?)$', rhs)
            if m:
                lat = float(m.group(1))
                lon = float(m.group(2))
                alias_to_coords[alias] = (lat, lon)
                continue

            if rhs:
                alias_to_address[alias] = rhs

    return alias_to_address, alias_to_coords


def resolve_alias(alias: str) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
    """Return (mapped_address, coords) for a given alias, if present."""
    addr_map, coord_map = parse_nonstandard_file()
    if alias in coord_map:
        return None, coord_map[alias]
    if alias in addr_map:
        return addr_map[alias], None
    return None, None
