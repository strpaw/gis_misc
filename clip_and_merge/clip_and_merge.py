"""Clip data from multiple files to given area of interest and
save it into one geopackage file.
"""
from dataclasses import dataclass
from pathlib import Path

from dacite import (
    from_dict,
    MissingValueError,
    WrongTypeError
)
from fiona.errors import DriverError
import geopandas as gpd
from yaml import safe_load


@dataclass(frozen=True)
class DataPaths:
    """Input/output data paths"""
    dir_input: str
    file_output: str


@dataclass(frozen=True)
class Aoi:
    """Area of interest definition"""
    epsg_code: int | str
    geometry: str


@dataclass(frozen=True)
class Configuration:
    """Script configuration"""
    data_paths: DataPaths
    aoi: Aoi
    file_ext: list[str]


def load_config() -> Configuration | Exception:
    """Return parsed config"""
    try:
        with open("config.yml", "r", encoding="utf-8") as f:
            content = safe_load(f)
            return from_dict(
                data_class=Configuration,
                data=content
            )
    except FileNotFoundError as e:
        raise FileNotFoundError from e
    except (MissingValueError, WrongTypeError) as e:
        raise ValueError(f"Config file error: {e}") from e


def main():
    """Main script loop"""
    # TODO: different CRS input, output
    config = load_config()
    aoi_gs = gpd.GeoSeries.from_wkt(data=[config.aoi.geometry],
                                    crs=config.aoi.epsg_code)
    data_path = Path(config.data_paths.dir_input)
    files = data_path.glob("**/*")
    for f in files:
        if f.is_dir():
            continue

        if f.suffix in config.file_ext:
            gdf = gpd.read_file(f, mask=aoi_gs)
            layer = gdf.clip(aoi_gs)
            print(f"File {f} clipped")
            layer.to_file(config.data_paths.file_output, layer=f"{f.stem}")


if __name__ == "__main__":
    main()
