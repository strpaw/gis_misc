"""Custom types"""
from typing import NamedTuple


class Ellipsoid(NamedTuple):
    """Ellipsoid parameters"""
    a: float  # major semi-axis
    b: float  # minor semi-axis
    f: float  # flattening


DecimalDegrees = float
Meters = float


class GeographicCoordinates(NamedTuple):
    """Point location"""
    lon: DecimalDegrees
    lat: DecimalDegrees
