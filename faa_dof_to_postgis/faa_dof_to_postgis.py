"""Script to load DOF (Digital Obstacle File) data from CSV file into PostgreSQL
database with PostGIS extension"""
import sys

import geopandas as gpd
import pandas as pd
from pydantic import BaseModel, ValidationError
from sqlalchemy import create_engine
from yaml import safe_load


Code = str
CodeDescription = str


class DBSettings(BaseModel):
    """Target database connection setting"""
    host: str
    database: str
    user: str
    password: str

class DOFDecoding(BaseModel):
    """DOF 'decoding rules'"""
    action: dict[Code, CodeDescription]
    lighting: dict[Code, CodeDescription]
    marking: dict[Code, CodeDescription]
    hor_acc: dict[Code, CodeDescription]
    vert_acc: dict[Code, CodeDescription]

class Configuration(BaseModel):
    """Script configuration"""
    db_settings: DBSettings
    dof_decoding: DOFDecoding


def load_config(path: str = "faa_dof_to_postgis_config.yaml") -> Configuration:
    """Load script configuration.

    :param path: path to the configuration file
    :return: script configuration
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = safe_load(f)
            return Configuration(**content)
    except (FileNotFoundError, ValidationError) as e:
        print(e)
        sys.exit(0)


def decode(row: pd.Series,
           column: str,
           decoding: dict[Code, CodeDescription]) -> str:
    """Decode obstacle codes for action, marking, lighting.

    :param row: row of data
    :param column:
    :param decoding: decoding mapping for specific column
    :return: description for corresponding code
    """
    return decoding.get(row[column], "NA")

def decode_hor_acc(row: pd.Series,
                   decoding: dict[Code, CodeDescription]) -> str:
    """Decode horizontal accuracy.

    :param row: single obstacle data
    :param decoding: decoding mapping for horizontal accuracy
    :return: decoded horizontal accuracy, e.g: 20ft
    """
    value = row["ACCURACY"].strip()
    if not value:
        return "NA"
    if len(value) != 2:
        return "NA"
    return decoding.get(value[0], "NA")


def decode_vert_acc(row: pd.Series,
                   decoding: dict[Code, CodeDescription]) -> str:
    """Decode vertical accuracy.

    :param row: single obstacle data
    :param decoding: decoding mapping for vertical accuracy
    :return: decoded vertical accuracy, e.g: 3ft
    """
    value = row["ACCURACY"].strip()
    if not value:
        return "NA"
    if len(value) != 2:
        return "NA"
    return decoding.get(value[1], "NA")


def lower_column_names(data: pd.DataFrame) -> None:
    """Change column names to lower case

    :param data: source data
    """
    cols = list(data.columns)
    mapping = {c: c.lower() for c in cols}
    data.rename(
        columns=mapping,
        inplace=True
    )


def prepare_data(
        dof_decoding: DOFDecoding,
        dof: str = "DOF.CSV"
) -> pd.DataFrame:
    """Prepare data before inserting into PostGIS:
     - add columns with decoded values for marking, lighting, horizontal accuracy etc.
     - change column names in source upper case to lower case

    :param dof_decoding: decoding rules for marking, lighting etc.
    :param dof: path to the source data
    :return: prepared data
    """
    df = pd.read_csv(dof)
    df["action_desc"] = df.apply(
        lambda row:decode(row, column="ACTION", decoding=dof_decoding.action),
        axis=1
    )
    df["lighting_desc"] = df.apply(
        lambda row: decode(row, column="LIGHTING", decoding=dof_decoding.lighting),
        axis=1
    )
    df["marking_desc"] = df.apply(
        lambda row: decode(row, column="MARKING", decoding=dof_decoding.marking),
        axis=1
    )
    df["hor_acc_desc"] = df.apply(
        lambda row: decode_hor_acc(row, decoding=dof_decoding.hor_acc),
        axis=1
    )
    df["vert_acc_desc"] = df.apply(
        lambda row: decode_vert_acc(row, decoding=dof_decoding.vert_acc),
        axis=1
    )
    lower_column_names(df)
    return df

def main() -> None:
    """Main script loop"""
    config = load_config()
    data = prepare_data(
        dof_decoding=config.dof_decoding,
        dof="DOF.csv"
    )
    gdf = gpd.GeoDataFrame(
        data=data,
        geometry=gpd.points_from_xy(data.londec, data.latdec),
        crs="EPSG:4326"
    )
    engine = create_engine(
        "postgresql+psycopg2://{user}:{password}@{host}:5432/{database}".format(**config.db_settings.model_dump()))
    with engine.connect() as con:
        con.execution_options(isolation_level="AUTOCOMMIT")
        gdf.to_postgis(
            name="obstacle",
            con=con,
            if_exists="append",
            index=False,
            chunksize=10000
        )


if __name__ == "__main__":
    main()
