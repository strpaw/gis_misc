"""Generate graticule"""
import argparse
from dataclasses import dataclass

from dacite import (
    from_dict,
    MissingValueError,
    WrongTypeError
)
import geopandas as gpd
from yaml import safe_load
from numpy import arange, linspace, full
from shapely import LineString

DEGREE = 1
_STEP = 0.1 * DEGREE


@dataclass(frozen=True)
class GraticuleLines:
    """Column names for coordinates"""
    start: int | float
    end: int | float
    step: int | float


@dataclass(frozen=True)
class Configuration:
    """Script configuration"""
    latitudes: GraticuleLines
    longitudes: GraticuleLines


def load_config(path: str = "config.yml") -> Configuration | Exception:
    """Return parsed config.

    :param path: path to the configuration file
    :return: parsed config
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = safe_load(f)
            return from_dict(
                data_class=Configuration,
                data=content
            )
    except FileNotFoundError as e:
        raise FileNotFoundError from e
    except (MissingValueError, WrongTypeError) as e:
        raise ValueError(f"Config file error: {e}") from e


def points_num(start: int | float,
               end: int | float) -> int | Exception:
    if start == end:
        raise ValueError("Start, end values are equal.")
    if start > end:
        raise ValueError("Start is less than end.")
    range_ = end - start
    return int(range_ / _STEP)


def meridians(lon_from: int | float,
              lon_to: int | float,
              lat_from: int | float,
              lat_to: int | float,
              step: int | float) -> tuple[list[str], list[LineString]]:
    """Return meridians geometries and its labels.

    :param lon_from: graticule min longitude
    :param lon_to: graticule max longitude
    :param lat_from: graticule min latitude
    :param lat_to: graticule max latitude
    :param step: meridians interval
    :return: list of meridian geometries
    """
    try:
        num = points_num(lat_from, lat_to)
    except Exception as e:
        raise ValueError(f"Invalid longitude range: {e}") from e

    labels, meridians_ = [], []
    coords_lat = linspace(start=lat_from, stop=lat_to, num=num, endpoint=True).tolist()
    for lon in arange(lon_from, lon_to + step, step):
        labels.append(f"LON {lon}")
        coords_lon = full((len(coords_lat)), lon).tolist()
        coords_meridian = list(zip(coords_lon, coords_lat))
        meridian = LineString(coords_meridian)
        meridians_.append(meridian)

    return labels, meridians_


def parallels(lon_from: int | float,
              lon_to: int | float,
              lat_from: int | float,
              lat_to: int | float,
              step: int | float) -> tuple[list[str], list[LineString]]:
    """Return parallels geometries and its labels.

    :param lon_from: graticule min longitude
    :param lon_to: graticule max longitude
    :param lat_from: graticule min latitude
    :param lat_to: graticule max latitude
    :param step: parallels interval
    :return: list of parallel geometries
    """
    try:
        num = points_num(lat_from, lat_to)
    except Exception as e:
        raise ValueError(f"Invalid longitude range: {e}") from e

    labels, parallels_ = [], []
    coords_lon = linspace(start=lon_from, stop=lon_to, num=num, endpoint=True).tolist()
    for lat in arange(lat_from, lat_to + step, step):
        labels.append(f"LAT {lat}")
        coords_lat = full((len(coords_lon)), lat).tolist()
        coords_parallel = list(zip(coords_lon, coords_lat))
        parallel = LineString(coords_parallel)
        parallels_.append(parallel)

    return labels, parallels_


def parse_args() -> argparse.Namespace:
    """Parse input arguments"""
    parser = argparse.ArgumentParser(
        prog="graticule_generator",
        description="Generates graticule lines"
    )

    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        required=True,
        help="path to the configuration file"
    )

    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        required=True,
        help="path to the output file"
    )

    return parser.parse_args()


def main():
    """Script main loop"""
    args = parse_args()
    config = load_config(args.config_file)
    mer_labels, mer = meridians(config.longitudes.start,
                                config.longitudes.end,
                                config.latitudes.start,
                                config.latitudes.end,
                                config.longitudes.step)
    par_labels, par = parallels(config.longitudes.start,
                                config.longitudes.end,
                                config.latitudes.start,
                                config.latitudes.end,
                                config.latitudes.step)
    data = {
        "deg": mer_labels + par_labels,
        "geometry": mer + par
    }
    gdf = gpd.GeoDataFrame(data=data, crs="EPSG:4326")
    gdf.to_file(args.output_file)


if __name__ == "__main__":
    main()
