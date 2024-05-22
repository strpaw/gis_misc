"""Geodesic calculations on ellipsoid"""
from math import (
    atan2,
    cos,
    degrees,
    fabs,
    pi,
    radians,
    sqrt,
    sin,
    tan
)

from _types import (
    Ellipsoid,
    DecimalDegrees,
    GeographicCoordinates,
    Meters
)
from ellipsoid import WGS84


def vincenty_direct_solution(initial_point: GeographicCoordinates,
                             initial_azimuth: DecimalDegrees,
                             distance: Meters,
                             ellipsoid: Ellipsoid = WGS84) -> GeographicCoordinates:
    """Computes the latitude and longitude of the second point based on latitude, longitude,
    of the first point and distance and azimuth from first point to second point.
    Uses the algorithm by Thaddeus Vincenty for direct geodetic problem.
    For more information refer to: http://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf.

    :param initial_point:
    :param initial_azimuth: azimuth from the initial point to the end point in decimal degrees format
    :param distance: distance from first point to second point; meters
    :param ellipsoid:
    :return: end point in decimal degrees format
    """
    a, b, f = ellipsoid
    lon1 = radians(initial_point.lon)
    lat1 = radians(initial_point.lat)
    alpha1 = radians(initial_azimuth)

    sin_alpha1 = sin(alpha1)
    cos_alpha1 = cos(alpha1)

    # U1 - reduced latitude
    tan_u1 = (1 - f) * tan(lat1)
    cos_u1 = 1 / sqrt(1 + tan_u1 * tan_u1)
    sin_u1 = tan_u1 * cos_u1

    # sigma1 - angular distance on the sphere from the equator to initial point
    sigma1 = atan2(tan_u1, cos(alpha1))

    # sin_alpha - azimuth of the geodesic at the equator
    sin_alpha = cos_u1 * sin_alpha1
    cos_sq_alpha = 1 - sin_alpha * sin_alpha
    u_sq = cos_sq_alpha * (a * a - b * b) / (b * b)
    A = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    B = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

    sigma = distance / (b * A)
    sigmap = 1
    sin_sigma, cos_sigma, cos2sigma_m = None, None, None

    while fabs(sigma - sigmap) > 1e-12:
        cos2sigma_m = cos(2 * sigma1 + sigma)
        sin_sigma = sin(sigma)
        cos_sigma = cos(sigma)
        d_sigma = B * sin_sigma * (cos2sigma_m + B / 4 * (
                    cos_sigma * (-1 + 2 * cos2sigma_m * cos2sigma_m) - B / 6 * cos2sigma_m * (
                        -3 + 4 * sin_sigma * sin_sigma) * (-3 + 4 * cos2sigma_m * cos2sigma_m)))
        sigmap = sigma
        sigma = distance / (b * A) + d_sigma

    var_aux = sin_u1 * sin_sigma - cos_u1 * cos_sigma * cos_alpha1  # Auxiliary variable

    # Latitude of the end point in radians
    lat2 = atan2(sin_u1 * cos_sigma + cos_u1 * sin_sigma * cos_alpha1,
                 (1 - f) * sqrt(sin_alpha * sin_alpha + var_aux * var_aux))

    lamb = atan2(sin_sigma * sin_alpha1, cos_u1 * cos_sigma - sin_u1 * sin_sigma * cos_alpha1)
    C = f / 16 * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))
    L = lamb - (1 - C) * f * sin_alpha * (
                sigma + C * sin_sigma * (cos2sigma_m + C * cos_sigma * (-1 + 2 * cos2sigma_m * cos2sigma_m)))

    # Longitude of the end point in radians
    lon2 = (lon1 + L + 3 * pi) % (2 * pi) - pi

    lon_end = degrees(lon2)
    lat_end = degrees(lat2)

    return GeographicCoordinates(lon=lon_end, lat=lat_end)
