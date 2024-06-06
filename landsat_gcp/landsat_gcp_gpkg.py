"""Convert Landsat Ground Control Point (GCP) plain text file into geopackage"""
from __future__ import annotations
import argparse
from dataclasses import dataclass

from dacite import (
    from_dict,
    MissingValueError,
    WrongTypeError
)
import geopandas as gpd
import pandas as pd
from yaml import safe_load


@dataclass(frozen=True)
class CoordinateColumns:
    """Column names for coordinates"""
    lon: str
    lat: str


@dataclass(frozen=True)
class Configuration:
    """Script configuration"""
    columns_definition_rows: int
    header_rows: int
    coordinates: CoordinateColumns


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


def get_columns_names(path: str,
                      nrows: int) -> list[str]:
    """Return `raw` column names - as they are in the header in the data file.

    :param path: path to the data file
    :param nrows: number of rows that contain column names
    :return: list of column names
    """
    with open(path, mode="r", encoding="utf-8") as f:
        return [next(f) for _ in range(nrows)]


def clean_column_names(columns: list[str]) -> list[str]:
    """Return column names without type, leading comment character

    Example column names in the data file:
    # Unique Ground Control Point (GCP) ID - integer
    # GCP Active Flag - string (Y/N)
    # GCP date updated - string in form mm-dd-yyyy
    # GCP update reason - string

    result:
    Unique Ground Control Point (GCP) ID
    GCP Active Flag
    GCP date updated
    GCP update reason

    :param columns: list of column names as they are in the header in the data file
    :return: list of column names as they will be used in the output file
    """
    def remove_column_type(column: str) -> str:
        """Remove column type

        :param column: column name as it in the data file
        :return: column name without column type
        """
        parts = column.split("-")[:-1]
        return "".join(parts)

    def clean_column(column: str) -> str:
        """Remove column type, leading comment character.

        :param column: column name as it in the data file
        :return: column name as it will be used in the output file
        """
        column = remove_column_type(column)
        return (column
                .replace("#", "")
                .strip())

    return [clean_column(c) for c in columns]


def to_geodata_frame(path: str,
                     columns: list[str],
                     config: Configuration) -> gpd.GeoDataFrame:
    """Returns GeoDataFrame from Landsat GCP plain text data.
    :param path: path to the file with Landsat GCP
    :param columns:
    :param config: parsed config file
    :return: GeoDataFrame with Landsat GCP
    """
    df = pd.read_csv(
        path,
        delimiter=r"\s",
        names=columns,
        skiprows=config.header_rows
    )
    df["geometry"] = gpd.GeoSeries.from_xy(x=df[config.coordinates.lon],
                                           y=df[config.coordinates.lat],
                                           crs="EPSG:4326")
    return gpd.GeoDataFrame(df)


def parse_args() -> argparse.Namespace:
    """Parse input arguments"""
    parser = argparse.ArgumentParser(
        prog="landsat_gcp_gpkg",
        description="Landsat GCP plain text file to geopackage"
    )

    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        required=True,
        help="path to the configuration file"
    )

    parser.add_argument(
        "-i",
        "--input-file",
        type=str,
        required=True,
        help="path to the data file"
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
    columns = get_columns_names(args.input_file, config.columns_definition_rows)
    columns = clean_column_names(columns)
    gdf = to_geodata_frame(path=args.input_file,
                           columns=columns,
                           config=config)
    gdf.to_file(args.output_file)


if __name__ == "__main__":
    main()
