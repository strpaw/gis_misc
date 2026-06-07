"""Script to generate special parallels (such as polar circles, tropics) for specific longitude ranges."""
from pathlib import Path

import numpy as np
import geopandas as gpd
import pandas as pd
from pydantic import BaseModel
from shapely.geometry import LineString
from yaml import safe_load


STEP_DEGREES = 0.1
PARALLELS = {
    "north_polar_circle": 66.5,
    "south_polar_circle": -66.5,
    "tropic_cancer": 23.5,
    "tropic_capricorn": -23.5
}


class ParallelsSetting(BaseModel):
    """
    Configuration flags controlling which special parallels will be generated.

    Attributes:
        north_polar_circle: Whether to generate the Arctic Circle
        south_polar_circle: Whether to generate the Antarctic Circle
        tropic_cancer: Whether to generate the Tropic of Cancer
        tropic_capricorn: Whether to generate the Tropic of Capricorn
    """
    north_polar_circle: bool
    south_polar_circle: bool
    tropic_cancer: bool
    tropic_capricorn: bool


class Longitudes(BaseModel):
    """
    Longitude range configuration.

    Attributes:
        start: Starting longitude value (degrees).
        end: Ending longitude value (degrees).
    """
    start: float | int
    end: float | int


class AppConfig(BaseModel):
    """
    Application configuration.

    Attributes:
        parallels: Parameters controlling which parallels will be generated.
        output: Path where generated results will be written.
        longitudes: Longitude range for generated parallels.
    """
    parallels: ParallelsSetting
    output: Path
    longitudes: Longitudes


def load_config(path: Path) -> AppConfig:
    """Load script configuration.

    :param path: path to the configuration file
    :return: Script configuration
    """
    content = safe_load(path.read_text(encoding="utf-8"))
    return AppConfig(**content)

def get_parallels_to_generate(parallels: ParallelsSetting) -> list[str]:
    """Return names of parallels to generate.

    :param parallels:
    :return: names of special parallels to generate
    """
    return [
        field
        for field, value in parallels.model_dump().items()
        if value
    ]


def gen_parallel(longitudes: np.ndarray,
                 latitude: float) -> LineString:
    """Generate single parallel line.

    :param longitudes: longitude values of the generated parallel
    :param latitude: latitude of parallel
    :return:
    """
    coords = [(lon, latitude) for lon in longitudes]
    return LineString(coords)

def main():
    config = load_config(path=Path("config.yaml"))
    parallels = get_parallels_to_generate(parallels=config.parallels)
    longitudes = np.arange(config.longitudes.start, config.longitudes.end + STEP_DEGREES, STEP_DEGREES)
    data = []
    for p in parallels:
        geom = gen_parallel(longitudes, PARALLELS[p])
        data.append(
            {
                "name": p,
                "geom": geom
            }
        )

    df = pd.DataFrame(data)
    gdf = gpd.GeoDataFrame(
        data=df,
        geometry=df.geom,
        crs="EPSG:4326"
    )
    gdf.drop(columns=["geom"], inplace=True)
    gdf.to_file(config.output, driver="GPKG")


if __name__ == "__main__":
    main()
