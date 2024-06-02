"""Create polygons based on CSV data files.
Each line of data file consists of:
<polygon name>;<vertex latitude>;<vertex longitude>
Input data file:
- field separator: ; (semicolon)
- fields:
    name: polygon name
    lat: latitude
    lon: longitude
"""
from typing import Literal
import re

import numpy as np
import geopandas as gpd
import pandas as pd
from shapely import Polygon


NEGATIVE_SIGN = ["S", "W"]

LONGITUDE_COMPACTED_PATTERN = re.compile(
    r"""^(?P<hem_prefix>[EW])?
         (?P<deg>\d{3})
         (?P<min>\d{2})
         (?P<sec>\d{2}|\d{2}\.\d+)
         (?P<hem_suffix>[EW])?$""",
    re.VERBOSE
)

LATITUDE_COMPACTED_PATTERN = re.compile(
    r"""^(?P<hem_prefix>[NS])?
         (?P<deg>\d{2})
         (?P<min>\d{2})
         (?P<sec>\d{2}|\d{2}\.\d+)
         (?P<hem_suffix>[NS])?$""",
    re.VERBOSE
)


class CoordinateError(Exception):
    """Raised when:
    - coordinate format is not supported (cannot be 'normalized' to 'compacted' HDMS or DMSH format)
    - coordinate is incorrect, e.g.: minute value is >= 60
    """
    def __init__(self, coordinate_type: Literal["Latitude", "Longitude"]):
        """
        :param coordinate_type: coordinate type that raises error: Latitude or Longitude
        """
        self.message = f"{coordinate_type} coordinate not supported format/coordinate value error"

    def __str__(self):
        return self.message


def coordinate_exception(func):
    """Handle coordinate conversion exception (not supported format, incorrect coordinate)"""
    def wrapper(coord):
        try:
            return func(coord)
        except CoordinateError as e:
            print(f"{e}: {coord}")
            return np.nan
    return wrapper


@coordinate_exception
def longitude_to_dd(lon: str) -> float:
    """Return longitude in decimal degrees (DD) format.
    Raise CoordinateValueError when there is error in coordinate (example minute is out of range <0, 60)
    or coordinate is in not supported format.

    :param lon: longitude in HDMS or DMSH compacted or space delimited format
    :return: decimal degrees
    """
    match = re.match(LONGITUDE_COMPACTED_PATTERN, lon)
    if not match:
        raise CoordinateError("Longitude")

    h = match.group("hem_prefix") or match.group("hem_suffix")
    d = int(match.group("deg"))
    m = int(match.group("min"))
    s = float(match.group("sec"))

    # hemisphere prefix and suffix cannot be both set
    # degrees within range <0, 180>
    # minutes and seconds  within range <0, 60)
    if any(
        [
            (match.group("hem_prefix") and match.group("hem_suffix")),
            not 0 <= d <= 180,
            not 0 <= m < 60,
            not 0 <= s < 60,
            d == 180 and (m != 0 or s != 0)
        ]
    ):
        raise CoordinateError("Longitude")

    dd = d + (m + s / 60) / 60
    if h in NEGATIVE_SIGN:
        return -dd
    return dd


@coordinate_exception
def latitude_to_dd(lat: str) -> float:
    """Return latitude in decimal degrees (DD) format.
    Raise CoordinateValueError when there is error in coordinate (example minute is out of range <0, 60)
    or coordinate is in not supported format.

    :param lat: latitude in HDMS or DMSH compacted or space delimited format
    :return: decimal degrees
    """
    match = re.match(LATITUDE_COMPACTED_PATTERN, lat)
    if not match:
        raise CoordinateError("Latitude")

    h = match.group("hem_prefix") or match.group("hem_suffix")
    d = int(match.group("deg"))
    m = int(match.group("min"))
    s = float(match.group("sec"))

    # hemisphere prefix and suffix cannot be both set
    # degrees within range <0, 90>
    # minutes and seconds  within range <0, 60)
    if any(
        [
            (match.group("hem_prefix") and match.group("hem_suffix")),
            not 0 <= d <= 90,
            not 0 <= m < 60,
            not 0 <= s < 60,
            d == 90 and (m != 0 or s != 0)
        ]
    ):
        raise CoordinateError("Latitude")

    dd = d + (m + s / 60) / 60
    if h in NEGATIVE_SIGN:
        return -dd
    return dd


def create_polygons(data: str) -> gpd.GeoDataFrame:
    """Returns polygons based on CSV data

    :param data: path to CSV data file
    :return: geodata frame with polygons
    """
    df = pd.read_csv(data, sep=";")
    df.ffill(inplace=True)

    df["lat"] = df.apply(lambda row: row.lat.upper().replace(" ", "").replace(",", "."), axis=1)
    df["lon"] = df.apply(lambda row: row.lon.upper().replace(" ", "").replace(",", "."), axis=1)
    df["lat_dd"] = df.apply(lambda row: latitude_to_dd(row.lat), axis=1)
    df["lon_dd"] = df.apply(lambda row: longitude_to_dd(row.lon), axis=1)

    df_errors = df.loc[df.isnull().any(axis=1)]
    errors = df_errors.name.unique()
    df.drop(df.loc[df.name.isin(errors)].index, inplace=True)
    errors = ",".join(errors)
    print(f"Following polygons will be skipped due to above coordinates errors: {errors}")

    poly_names, poly_geoms = [], []

    for asp_name in df.name.unique():
        asp_data = df.loc[df.name == asp_name]
        lon, lat = asp_data.lon_dd.to_list(), asp_data.lat_dd.to_list()
        coords = list(zip(lon, lat))
        geometry = Polygon(coords)

        poly_names.append(asp_name)
        poly_geoms.append(geometry)

    return gpd.GeoDataFrame(
        data={
            "name": poly_names,
            "geometry": poly_geoms
        },
        geometry="geometry",
        crs="EPSG:4326"
    )
