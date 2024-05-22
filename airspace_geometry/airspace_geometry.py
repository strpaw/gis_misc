"""Functions to calculate airspace geometries"""
from math import ceil, floor

from shapely.geometry import Polygon

from _exceptions import RadiiError
from _types import (
    DecimalDegrees,
    GeographicCoordinates,
    Meters,
)
from geodesic_calc import vincenty_direct_solution


def _central_int_angle(azimuth_from: DecimalDegrees,
                       azimuth_to: DecimalDegrees) -> int | Exception:
    """Return the central angle between two azimuths.

    :param azimuth_from: Beginning of the angle
    :param azimuth_to: End of the angle
    :return: central angle
    """
    a = ceil(azimuth_to) - floor(azimuth_from)
    return a % 360


def _circle_coords(center: GeographicCoordinates,
                   radius: Meters) -> list[GeographicCoordinates]:
    """Return list of coordinates that form circle.

    :param center: Circle center coordinates
    :param radius: Circle radius
    :return: Circle coordinates
    """
    return [vincenty_direct_solution(center, i, radius) for i in range(360)]


def _arc_coords(center: GeographicCoordinates,
                radius: Meters,
                azimuth_from: DecimalDegrees,
                azimuth_to: DecimalDegrees) -> list[GeographicCoordinates]:
    """Return list of coordinates that from arc.

    :param center: Arc center coordinates
    :param radius: Arc radius
    :param azimuth_from: Beginning azimuth of the arc
    :param azimuth_to: End azimuth of the arc
    :return: Arc coordinates
    """
    arc_begin = vincenty_direct_solution(center, azimuth_from, radius)
    arc_end = vincenty_direct_solution(center, azimuth_to, radius)

    coords = [arc_begin]
    angle = _central_int_angle(azimuth_from, azimuth_to)
    azm_ = floor(azimuth_from)
    for i in range(1, angle):
        azm = azm_ + i
        if azm > 360:
            azm -= 360
        p = vincenty_direct_solution(center, azm, radius)
        coords.append(p)
    coords.append(arc_end)
    return coords


def circle(center: GeographicCoordinates,
           radius: Meters) -> Polygon:
    """Return geometry for airspace with circle shape.

    :param center: Center of the circle coordinates
    :param radius: Circle radius
    :return: Circle polygon
    """
    coords = _circle_coords(center, radius)
    return Polygon(coords)


def circular_sector(center: GeographicCoordinates,
                    radius: Meters,
                    azimuth_from: DecimalDegrees,
                    azimuth_to: DecimalDegrees) -> Polygon:
    """Return geometry for airspace with circular sector shape.

    :param center: Center of the circular sector
    :param radius: Radius of the circular sector
    :param azimuth_from: Beginning azimuth of the circular sector
    :param azimuth_to: Final azimuth of the circular sector
    :return: Circular sector polygon
    """

    coords = [center]
    arc = _arc_coords(center, radius, azimuth_from, azimuth_to)
    coords.extend(arc)
    return Polygon(coords)


def circular_segment(center: GeographicCoordinates,
                     radius: Meters,
                     azimuth_from: DecimalDegrees,
                     azimuth_to: DecimalDegrees) -> Polygon:
    """Return geometry for airspace with circular segment shape.

    :param center: Center of the circular segment
    :param radius: Radius of the circular sector
    :param azimuth_from: Beginning azimuth of the circular segment
    :param azimuth_to: Final azimuth of the circular segment
    :return: Circular segment polygon
    """
    arc = _arc_coords(center, radius, azimuth_from, azimuth_to)
    return Polygon(arc)


def ring(center: GeographicCoordinates,
         inner_radius: Meters,
         outer_radius: Meters) -> Polygon | ValueError:
    """Return geometry for airspace with ring shape.

    :param center: Center of the ring
    :param inner_radius: Ring inner radius
    :param outer_radius: Ring outer radius
    :return: Ring polygon
    """
    if inner_radius >= outer_radius:
        raise ValueError("Inner radius must be less than outer radius")
    inner_circle = _circle_coords(center, inner_radius)
    outer_circle = _circle_coords(center, outer_radius)
    return Polygon(shell=outer_circle, holes=[inner_circle])


def ring_sector(center: GeographicCoordinates,
                inner_radius: Meters,
                outer_radius: Meters,
                azimuth_from: DecimalDegrees,
                azimuth_to: DecimalDegrees) -> Polygon | ValueError:
    """Return geometry for airspace with ring segment shape.

    :param center: Center of the ring sector
    :param inner_radius: Ring sector inner radius
    :param outer_radius: Ring sector outer radius
    :param azimuth_from: Beginning azimuth of the ring sector
    :param azimuth_to: Final azimuth of the ring sector
    :return: Ring sector polygon
    """
    if inner_radius >= outer_radius:
        raise RadiiError("Inner radius must be less than outer radius")

    outer_arc = _arc_coords(center, outer_radius, azimuth_from, azimuth_to)
    #  Revers inner arc, to make clock-wise coordinates order
    inner_arc = list(reversed(_arc_coords(center, inner_radius, azimuth_from, azimuth_to)))
    coords = outer_arc + inner_arc
    return Polygon(coords)
